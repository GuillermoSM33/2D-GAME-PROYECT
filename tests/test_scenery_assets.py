"""Native scenery contracts, paired occupation marks and reproducible source art."""
from pathlib import Path
import math
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from embed_assets import decode_png_rgba
import make_props
import make_houses
import make_city
import make_car_passage
import make_terrain
from refine_terrain import refine
from terrain_architecture_detail import street_scale
import train_art


class SceneryArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated={**make_props.build_assets(),**make_houses.build_assets(),
                       **make_car_passage.build_assets()}
        source=make_city.make_city_fronts(marked=False)
        cls.front_source=street_scale('city_fronts',source)
        cls.fronts=refine('city_fronts',source)
        cls.generated['sprites/terrain/city_fronts.png']=cls.fronts
        cls.generated['sprites/terrain/facades.png']=refine('facades',make_terrain.make_facades())
        cls.generated['sprites/terrain/train.png']=refine('train',make_city.make_train())
        cls.generated['sprites/terrain/train_interior.png']=train_art.make_interior()
        cls.generated['sprites/terrain/experimental_parts.png']=train_art.make_parts()
        cls.generated['sprites/terrain/train_gear.png']=train_art.make_gear()

    def test_sources_reproduce_the_installed_sheets(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'sheet.png'
            for name,img in self.generated.items():
                with self.subTest(sheet=name):
                    img.save(p)
                    self.assertEqual(p.read_bytes(),(ROOT/'assets'/name).read_bytes())

    def test_prop_frame_sizes_and_emissive_alpha(self):
        for name,(w,h,count,_) in make_props.SPECS.items():
            width,height,px=decode_png_rgba(ROOT/f'assets/sprites/props/{name}.png')
            with self.subTest(prop=name):
                self.assertEqual((width,height),(w*count,h))
                self.assertTrue(set(px[3::4])<={0,254,255})
                if name in ('streetlight','signal','traffic_light'):
                    self.assertIn(254,px[3::4])

    def test_dead_trees_are_whole_matte_connected_silhouettes(self):
        art=self.generated['sprites/props/dead_tree.png']
        for variant in range(2):
            points={(x,y) for y in range(150) for x in range(100) if art.get(variant*100+x,y)[3]}
            todo=[next(iter(points))];seen=set(todo)
            while todo:
                x,y=todo.pop()
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        p=(x+dx,y+dy)
                        if p in points and p not in seen:seen.add(p);todo.append(p)
            self.assertEqual(seen,points,'A branch detached from the tree')
            self.assertTrue(all(0<x<99 and y>0 for x,y in points))
            colors=[art.get(variant*100+x,y) for x,y in points]
            self.assertLess(max(.299*r+.587*g+.114*b for r,g,b,_ in colors),180)

    def test_eight_fronts_each_have_an_identical_unpainted_building(self):
        art=self.fronts
        self.assertEqual((art.width,art.height),(16*288,216))
        for building in range(8):
            changed=0
            for y in range(216):
                for x in range(288):
                    a=art.get(building*288+x,y);b=art.get((building+8)*288+x,y)
                    self.assertEqual(a[3],b[3])
                    changed+=a!=b
            self.assertGreater(changed,40)
            self.assertLess(changed,2400)

    def test_central_passage_is_preserved_by_finishing(self):
        for frame in range(16):
            for y in range(152,216):
                for x in range(122,166):
                    before=self.front_source.get(frame*288+x,y)
                    after=self.fronts.get(frame*288+x,y)
                    self.assertEqual(after[3],before[3])
                    # The police steps occupy the last two rows and can shade;
                    # the actual aperture/empty road must remain byte-identical.
                    if y<214 or frame%8!=1:self.assertEqual(after,before)

    def test_train_is_thirteen_complete_cars_with_connected_running_gear(self):
        art=self.generated['sprites/terrain/train.png']
        rooms=train_art.ROOMS
        self.assertEqual((rooms,train_art.CARS),(15,13))
        self.assertEqual((art.width,art.height),(rooms*360+32,192))
        for car in range(train_art.CARS):
            start=16+car*360
            self.assertTrue(art.get(start+20,40)[3])
            self.assertTrue(art.get(start+39,187)[3])
            self.assertTrue(art.get(start+352,168)[3],'Missing coupler between cars')
        # Both ends fit inside the texture; the ground rail alone reaches its edges.
        for x in (0,art.width-1):
            self.assertFalse(any(art.get(x,y)[3] for y in range(188)))
        interior=self.generated['sprites/terrain/train_interior.png']
        self.assertEqual((interior.width,interior.height),(rooms*360,270))
        self.assertTrue(all(p[3]==255 for p in interior.px),'Interior tile has a cut or hole')
        for room in range(rooms):
            for y in range(240,270):
                self.assertEqual(interior.get(room*360,y),interior.get(((room+1)%rooms)*360,y))

    def test_train_spots_match_the_game_and_parts_are_distinct(self):
        import re
        header=(ROOT/'src/game/train.h').read_text(encoding='utf-8')
        value=lambda name:int(re.search(r'#define '+name+r'\s+(\d+)',header).group(1))
        self.assertEqual(value('TRAIN_ENTRY_ART'),train_art.ENTRY_X)
        self.assertEqual(value('TRAIN_CRADLE_ART'),train_art.CRADLE_X)
        self.assertEqual(value('TRAIN_TERMINAL_ART'),train_art.TERMINAL_X)
        self.assertEqual(value('TRAIN_EXIT_ART'),train_art.EXIT_X)
        self.assertEqual(value('TRAIN_SUIT_ART'),train_art.SUIT_X)
        self.assertEqual(value('TRAIN_SUIT_HOOK'),train_art.SUIT_HOOK)
        self.assertEqual(value('TRAIN_SUIT_BOTTOM'),train_art.SUIT_BOTTOM)
        self.assertEqual(value('TRAIN_TABLET_ART'),train_art.TABLET_X)
        self.assertEqual(value('TRAIN_TABLET_BOTTOM'),train_art.TABLET_BOTTOM)
        self.assertEqual((value('TRAIN_GEAR_W'),value('TRAIN_GEAR_H')),(train_art.tf.GEAR_W,train_art.tf.GEAR_H))
        config=(ROOT/'src/config.h').read_text(encoding='utf-8')
        self.assertEqual(int(re.search(r'#define TRAIN_ROOMS (\d+)',config).group(1)),train_art.ROOMS)
        self.assertEqual(int(re.search(r'#define TRAIN_CARS (\d+)',config).group(1)),train_art.CARS)
        interior=self.generated['sprites/terrain/train_interior.png']
        # Each part's cradle is lit where the part rests; the hatch has its socket.
        for room in train_art.CRADLE_ROOMS:
            self.assertEqual(interior.get(room*360+train_art.CRADLE_X,212)[:3],(0x9f,0xe8,0xe0))
        lamp=value('TRAIN_EXIT_LAMP_ART')
        self.assertLess(sum(interior.get((train_art.ROOMS-1)*360+lamp,167)[:3]),120)
        # Car 01: the suits hang from their hooks; the tablet stands on its
        # shelf, and the shelf is solid under it.
        gear=self.generated['sprites/terrain/train_gear.png']
        self.assertEqual((gear.width,gear.height),(2*32,80))
        for frame in range(2):
            rows=[y for y in range(80) for x in range(32) if gear.get(frame*32+x,y)[3]]
            self.assertEqual(max(rows),79,'Gear must stand on its bottom row')
            cols=[x for y in range(80) for x in range(32) if gear.get(frame*32+x,y)[3]]
            self.assertLessEqual(abs((min(cols)+max(cols))/2-15.5),1.5,'Gear is centred on its column')
        suit_top=min(y for y in range(80) for x in range(32) if gear.get(x,y)[3])
        top_row=train_art.SUIT_BOTTOM-80+suit_top
        self.assertTrue(167<=top_row<=173,'A human-sized suit hangs from a reachable hook')
        wall=interior.get(train_art.SUIT_X,171)
        for side in (-1,1):
            hook=train_art.SUIT_X+side*train_art.SUIT_HOOK
            self.assertNotEqual(interior.get(hook,171),wall,'Its hook is drawn there')
        shelf=train_art.TABLET_BOTTOM
        for dx in range(-8,9):
            self.assertGreater(sum(interior.get(train_art.TABLET_X+dx,shelf+1)[:3]),2*sum(interior.get(train_art.TABLET_X+dx,shelf+8)[:3]),'The tablet stands on its shelf, lit over the dark locker')
        parts=self.generated['sprites/terrain/experimental_parts.png']
        self.assertEqual((parts.width,parts.height),(8*32,32))
        shapes=[]
        for part in range(8):
            mask=frozenset((x,y) for y in range(32) for x in range(32) if parts.get(part*32+x,y)[3])
            self.assertGreater(len(mask),180,'A part too small to read in the room')
            self.assertFalse(any(x in (0,31) or y in (0,31) for x,y in mask),'Part touches its cell')
            shapes.append(mask)
        self.assertEqual(len(set(shapes)),8,'Two parts share a silhouette')

    def test_train_furniture_and_gear_are_human_scaled(self):
        """The train stays large; a seat, rifle, fridge and suit fit its crew."""
        person=67  # PLAYER_WALK_FRAME_H, shared by both characters
        gear=self.generated['sprites/terrain/train_gear.png']
        rows=[y for y in range(80) for x in range(32) if gear.get(x,y)[3]]
        self.assertLessEqual(max(rows)-min(rows)+1,person)
        room=train_art.Room(0)
        train_art.chair(room,60)
        rows=[y for y in range(240) for x in range(50,90) if room.get(x,y) is not None]
        self.assertLessEqual(max(rows)-min(rows)+1,person*.6)
        room=train_art.Room(0)
        train_art.tf.rifle(room,60,100)
        rows=[y for y in range(240) for x in range(50,90) if room.get(x,y) is not None]
        self.assertLessEqual(max(rows)-min(rows)+1,person*.65)
        room=train_art.Room(9)
        train_art.tf.room_mess(room)
        # Left edge of the fridge excludes the wall signs above it.
        rows=[y for y in range(150,240) if room.get(26,y) is not None]
        self.assertLessEqual(max(rows)-min(rows)+1,person*1.15)
        self.assertGreater(min(rows),150)

    def test_train_supply_bays_stay_clear_of_furniture(self):
        """Real crate rectangles remain clear in the native background art."""
        self.assertEqual(set(train_art.SUPPLY_BAYS),{1,3,5,7,8,9,11})
        for index,cx in train_art.SUPPLY_BAYS.items():
            room=train_art.Room(index)
            train_art.shell(room)
            footprint={(x,y):room.get(x,y) for y in range(204,236)
                       for x in range(cx-16,cx+16)}
            train_art.ROOM_ART[index](room)
            train_art.tf.room_dressing(room)
            with self.subTest(room=index+1):
                self.assertTrue(all(room.get(x,y)==col for (x,y),col in footprint.items()),
                                'Furniture or decoration crosses the playable crate bay')

    def test_clinical_curtains_are_supported_and_reveal_their_cots(self):
        """Curtains attach continuously to ceiling hardware and almost reach
        the floor; their opening shows a human-sized bed rather than wall."""
        for room_index,left,right in ((3,25,112),(10,137,218)):
            room=train_art.Room(room_index)
            train_art.shell(room)
            train_art.ROOM_ART[room_index](room)
            train_art.tf.room_dressing(room)
            with self.subTest(room=room_index+1):
                # Both steel drops run from their bolted plates to the rail.
                for x in (left+3,right-3):
                    for y in range(62,145):
                        if not 136<=y<=140: # Clamps surround the hanger here.
                            self.assertEqual(room.get(x,y),train_art.hx(0xa4b1a8))
                self.assertEqual(room.get(left+2,151),train_art.hx(0x8b9e92))
                self.assertNotEqual(room.get(left+4,232),train_art.WAINSCOT)
                mid=(left+right)//2
                self.assertGreater(sum(room.get(mid,212)),sum(room.get(mid,224)))

    def test_extractor_housings_match_the_renderer_coordinates(self):
        self.assertEqual(len(train_art.VENT_FANS),5)
        for index,cx,cy in train_art.VENT_FANS:
            room=train_art.Room(index)
            train_art.tf.extractor_housing(room,cx,cy)
            self.assertEqual(room.get(cx,cy),train_art.hx(0x142522))
            self.assertIsNotNone(room.get(cx-9,cy-9))
            self.assertIsNotNone(room.get(cx+9,cy+9))

    def test_open_doors_remove_the_original_glass_and_cover_the_player(self):
        M=make_car_passage
        kinds,w,h=M.C['CAR_DOOR_KINDS'],M.CAR_W,M.CAR_H
        self.assertEqual((w,h),(make_city.CAR_W,make_city.CAR_H),'The doors are drawn on the cars at their scale')
        for damage,suffix in enumerate(('', '_damaged')):
            body=self.generated[f'sprites/terrain/car_passage{suffix}.png']
            front=self.generated[f'sprites/terrain/car_passage{suffix}_front.png']
            self.assertEqual(body.width,3*3*kinds*w)
            for look in range(3):
                for side,doors in ((0,2),(1,4)):
                    leaf=M.door_leaf(look,side,damage,False)
                    points={(x,y) for y in range(h) for x in range(w) if leaf.solid(x,y)}
                    self.assertTrue(any(y<M.CY(14) for x,y in points),'Missing moving window frame')
                    self.assertTrue(any(y>M.CY(32) for x,y in points),'Missing lower door panel')
                    at0=(look*3*kinds+doors)*w
                    for x,y in points:
                        self.assertEqual(body.get(at0+x,y),front.get(at0+x,y),'Door leaf must cover the character')
                    # An unobstructed part of each former window is now cabin, open in the front.
                    shell,glass,hinge,latch=M.door_shapes(look,side,damage)
                    x,y=latch+3,M.CY(8+damage)
                    self.assertEqual(body.get(at0+x,y)[:3],(24,35,41))
                    self.assertEqual(front.get(at0+x,y)[3],0)
                # Glass, whole or broken out, covers her: in the car she is out of
                # sight but in an open door (the user saw her hat through it).
                for broken in (1,2):
                    shell,glass,hinge,latch=M.door_shapes(look,broken-1,damage)
                    x,y=latch+3,M.CY(9+damage)
                    at0=(look*3*kinds+broken*kinds)*w
                    self.assertEqual(front.get(at0+x,y)[3],255)
                    self.assertEqual(front.get(at0+x,y)[:3],body.get(at0+x,y)[:3])
                    self.assertEqual(front.get(look*3*kinds*w+x,y)[3],255)

    def test_car_frames_are_whole_in_one_row(self):
        """Each frame has all of her in one row of her sheet, out of the car or
        in it: never an arm, a leg or half of her left alone in the other (the
        user saw loose pieces in the sheet)."""
        frames=make_car_passage.C['CAR_PASS_FRAMES']
        for name,art in self.generated.items():
            if '/characters/' not in name:continue
            for frame in range(frames):
                rows=[any(art.get(frame*81+x,row*80+y)[3] for y in range(80) for x in range(81)) for row in (0,1)]
                self.assertEqual(sum(rows),1,f'{name} frame {frame}')

    def test_car_arms_never_fold_up(self):
        """Every hand is where an arm reaches it without folding up on itself
        (the user saw her arms broken going through the door). The SWAT's
        hand on his gun's sling, at his shoulder, is the one fold."""
        M,C=make_car_passage,make_car_passage.C
        for who,kind in (('cowgirl','rifle'),('swat','rifle')):
            fig=M.Figure(who,kind)
            for i,pose in enumerate(M.poses(fig)):
                M.render(fig,pose)
                sling=C['CAR_SETTLE_FIRST']<=i<C['CAR_REACH_FIRST'] or i>=C['CAR_READY_FIRST']
                if who=='swat' and sling:continue
                self.assertGreaterEqual(min(pose.reaches),M.MIN_REACH,f'{who} frame {i}')

    def test_car_legs_are_full_and_pass_each_other(self):
        """As thick as on her other sheets, and each hip goes with its foot: the user saw them
        thin and crossing from nowhere."""
        M=make_car_passage
        for who,least in (('cowgirl',6.0),('swat',7.5)):
            fig=M.Figure(who)
            for i,pose in enumerate(M.poses(fig)[:M.C['CAR_WALK_FRAMES']]):
                far,near=(M.chain(fig,pose,foot,3,0) for foot in (pose.far,pose.near))
                apart=(near[0][0]-far[0][0])*(pose.near[0]-pose.far[0])
                self.assertGreaterEqual(apart,0,f'{who} frame {i}: her legs cross')
                for joints in (far,near):
                    px=M.limb(fig,joints,False)
                    (x0,y0),(x1,y1)=joints[0],joints[1]
                    at=((x0+x1)/2,(y0+y1)/2)
                    length=math.hypot(x1-x0,y1-y0) or 1
                    nx,ny=-(y1-y0)/length,(x1-x0)/length
                    wide=sum(.25 for k in range(-40,41)
                             if (math.floor(at[0]+nx*k*.25),math.floor(at[1]+ny*k*.25)) in px)
                    self.assertGreaterEqual(wide,least-1,f'{who} frame {i}: a thin thigh')

    def test_car_poses_keep_pixels_inside_their_cells(self):
        frames=make_car_passage.C['CAR_PASS_FRAMES']
        for name,art in self.generated.items():
            self.assertLessEqual(art.width,8192,'Windows SDL texture limit')
            if '/characters/' not in name:continue
            self.assertEqual((art.width,art.height),(frames*81,160))
            for frame in range(frames):
                self.assertTrue(any(art.get(frame*81+x,y)[3] for y in range(160) for x in range(81)))
                self.assertFalse(any(art.get(frame*81+x,y)[3] for y in range(160) for x in (0,80)))
                # What is in the car never reaches below its floor (the road shows there).
                self.assertFalse(any(art.get(frame*81+x,80+y)[3] for y in range(make_car_passage.FLOOR+1,80)
                                     for x in range(81)))

    def test_car_steps_follow_the_game(self):
        """The sheet is cut into the steps of src/game/car_pass.h, in its order."""
        C=make_car_passage.C
        at=0
        for name,_ in make_car_passage.STEPS:
            self.assertEqual(C[f'CAR_{name}_FIRST'],at,name)
            at+=C[f'CAR_{name}_FRAMES']
        self.assertEqual(at,C['CAR_PASS_FRAMES'])


if __name__=='__main__':unittest.main()
