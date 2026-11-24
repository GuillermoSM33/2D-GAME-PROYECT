#include "game/train_render.h"

#include <math.h>
#include <stdio.h>
#include "engine/assets.h"
#include "game/hud.h"
#include "game/ui.h"

#define PART_PX 32 /* experimental_parts.png: one 32 x 32 frame per part */

static void color(SDL_Renderer *r, unsigned rgb, Uint8 alpha)
{
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, alpha);
}

static void rect(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb, Uint8 alpha)
{
    SDL_Rect box = {x, y, w, h};
    color(r, rgb, alpha);
    SDL_RenderFillRect(r, &box);
}

/* A soft additive light (sprites/effects/glow) centred on x, y. */
static void glow(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb, float strength)
{
    SDL_Texture *tex = assets_texture("sprites/effects/glow");
    if (!tex || strength <= 0.0f) return;
    Uint8 alpha, red, green, blue;
    SDL_BlendMode blend;
    SDL_GetTextureAlphaMod(tex, &alpha);
    SDL_GetTextureColorMod(tex, &red, &green, &blue);
    SDL_GetTextureBlendMode(tex, &blend);
    SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_ADD);
    SDL_SetTextureColorMod(tex, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb);
    SDL_SetTextureAlphaMod(tex, (Uint8)fminf(255.0f, 255.0f * strength));
    SDL_Rect dst = {x - w / 2, y - h / 2, w, h};
    SDL_RenderCopy(r, tex, NULL, &dst);
    SDL_SetTextureAlphaMod(tex, alpha);
    SDL_SetTextureColorMod(tex, red, green, blue);
    SDL_SetTextureBlendMode(tex, blend);
}

/* ---- The rooms ------------------------------------------------------------ */

static void ventilation(SDL_Renderer *r, const StageRun *run, float camera, float time)
{
    static const struct { int room, x, y; } fans[] = {
#define VENT_FAN(room, x, y) {room, x, y},
        TRAIN_VENT_FANS(VENT_FAN)
#undef VENT_FAN
    };
    const int px = SPRITE_SCALE;
    for (size_t i = 0; i < sizeof(fans) / sizeof(fans[0]); i++) {
        int cx = (int)lroundf(train_room_left(run, fans[i].room) + fans[i].x * px - camera);
        if (cx < -9 * px || cx > VIEW_WIDTH + 9 * px) continue;
        int cy = fans[i].y * px;
        float turn = time * (4.0f + (float)i * .4f) + (float)i;
        /* Only the inset rotor moves; its housing and wall brackets belong
         * to the native room art. Three broad blades remain crisp pixels. */
        for (int y = -5; y <= 5; y++) {
            for (int x = -5; x <= 5; x++) {
                int radius = x * x + y * y;
                if (radius > 25) continue;
                unsigned ink = 0x182222;
                if (radius <= 2) ink = 0x9aa59a;
                else if (cosf(3.0f * (atan2f((float)y, (float)x) - turn)) > .25f)
                    ink = x + y < 0 ? 0x85918a : 0x56635d;
                rect(r, cx + x * px, cy + y * px, px, px, ink, 255);
            }
        }
    }
}

void train_render_background(SDL_Renderer *r, const StageRun *run, float camera, float time)
{
    SDL_SetRenderDrawColor(r, 16, 20, 23, 255);
    SDL_RenderClear(r);
    SDL_Texture *sheet = assets_texture("sprites/terrain/train_interior");
    if (!sheet) return;
    int width = TRAIN_ROOM_W * SPRITE_SCALE;
    for (int room = 0; room < TRAIN_ROOMS; room++) {
        int x = (int)lroundf(run->train.left + room * width - camera);
        if (x + width < 0 || x > VIEW_WIDTH) continue;
        SDL_Rect src = {room * TRAIN_ROOM_W, 0, TRAIN_ROOM_W, TRAIN_INTERIOR_H};
        SDL_Rect dst = {x, 0, width, TRAIN_INTERIOR_H * SPRITE_SCALE};
        SDL_RenderCopy(r, sheet, &src, &dst);
    }
    ventilation(r, run, camera, time);
}

/* ---- In the world ------------------------------------------------------------ */

/* A brass chevron pointing down at what to use, bobbing; view px. */
static void chevron(SDL_Renderer *r, int cx, int bottom, float time, unsigned rgb)
{
    const int s = SPRITE_SCALE;
    int bob = (int)lroundf((sinf(time * 4.0f) + 1.0f) * 1.5f) * s;
    int y = bottom - 7 * s - bob;
    static const int rows[][2] = {{-4, 4}, {-3, 3}, {-2, 2}, {-1, 1}, {0, 0}};
    for (int k = 0; k < 5; k++) { /* Dark contour, then the fill */
        int a = rows[k][0], b = rows[k][1];
        rect(r, cx + (a - 1) * s, y + k * s - s, (b - a + 3) * s, 3 * s, 0x14100c, 255);
    }
    for (int k = 0; k < 5; k++) {
        int a = rows[k][0], b = rows[k][1];
        rect(r, cx + a * s, y + k * s, (b - a + 1) * s, s, k == 0 ? 0xf6e2a8 : rgb, 255);
    }
}

static void draw_part(SDL_Renderer *r, int part, int cx, int bottom, float time)
{
    SDL_Texture *sheet = assets_texture("sprites/terrain/experimental_parts");
    int size = PART_PX * SPRITE_SCALE;
    float pulse = .5f + .5f * sinf(time * 3.0f);
    int bob = (int)lroundf((sinf(time * 2.5f) + 1.0f)) * SPRITE_SCALE;
    int y = bottom - size - bob;
    /* A column of light over it, then a halo, so it reads across the room. */
    for (int k = 0; k < 6; k++)
        glow(r, cx, y - 40 - k * 70, 70 - k * 6, 150, 0x82e6dc, .22f - k * .03f);
    glow(r, cx, y + size / 2, size * 3, size * 2, 0x7fe0d6, .55f + .25f * pulse);
    if (sheet) {
        SDL_Rect src = {part * PART_PX, 0, PART_PX, PART_PX};
        SDL_Rect dst = {cx - size / 2, y, size, size};
        SDL_RenderCopy(r, sheet, &src, &dst);
    }
    glow(r, cx, y + size / 2, size, size, 0xffffff, .12f + .1f * pulse);
    chevron(r, cx, y - 6 * SPRITE_SCALE, time, 0x8fe8de);
}

/* A frame of sprites/terrain/train_gear, centred on art column x of car 01
 * and standing on art row bottom. */
static void gear(SDL_Renderer *r, const StageRun *run, int frame, float x, int bottom, float camera)
{
    SDL_Texture *sheet = assets_texture("sprites/terrain/train_gear");
    if (!sheet) return;
    int cx = (int)lroundf(run->train.left + x * SPRITE_SCALE - camera);
    if (cx < -200 || cx > VIEW_WIDTH + 200) return;
    SDL_Rect src = {frame * TRAIN_GEAR_W, 0, TRAIN_GEAR_W, TRAIN_GEAR_H};
    SDL_Rect dst = {cx - TRAIN_GEAR_W * SPRITE_SCALE / 2,
                    BASELINE - (GROUND_ROW - bottom + TRAIN_GEAR_H) * SPRITE_SCALE,
                    TRAIN_GEAR_W * SPRITE_SCALE, TRAIN_GEAR_H * SPRITE_SCALE};
    SDL_RenderCopy(r, sheet, &src, &dst);
}

void train_render_world(SDL_Renderer *r, const StageRun *run, const Player *player, float camera, float time)
{
    bool train_stage = run->stage_index == TRAIN_STAGE && run->train.present;
    if (train_stage && run->train.inside) {
        /* The broken tanks' air: slow clouds low over the floor, sickly green
         * in the cultures (03), colder in the cryo car (07). */
        for (int room = 0; room < TRAIN_ROOMS; room++) {
            if (!train_room_toxic(room)) continue;
            float left = train_room_left(run, room) - camera;
            if (left > VIEW_WIDTH || left + TRAIN_ROOM_W * SPRITE_SCALE < 0) continue;
            unsigned ink = room == 2 ? 0x7fd45a : 0x8fe0c8;
            for (int k = 0; k < 7; k++) {
                float drift = sinf(time * .35f + (float)k * 1.9f);
                int cx = (int)lroundf(left + (40.0f + (float)k * 48.0f + 14.0f * drift) * SPRITE_SCALE);
                int cy = BASELINE - (int)lroundf((22.0f + 8.0f * sinf(time * .5f + (float)k)) * SPRITE_SCALE);
                glow(r, cx, cy, 420, 200, ink, .34f + .08f * sinf(time * .8f + (float)k * 2.3f));
            }
        }
        /* Two suits on their hooks, one gone while she wears it; the tablet
         * in its locker until she takes it, its screen breathing. */
        gear(r, run, 0, TRAIN_SUIT_ART - TRAIN_SUIT_HOOK, TRAIN_SUIT_BOTTOM, camera);
        if (!run->train.suit) gear(r, run, 0, TRAIN_SUIT_ART + TRAIN_SUIT_HOOK, TRAIN_SUIT_BOTTOM, camera);
        if (!run->train.tablet) {
            gear(r, run, 1, TRAIN_TABLET_ART, TRAIN_TABLET_BOTTOM, camera);
            int cx = (int)lroundf(train_tablet_x(run) - camera);
            glow(r, cx, BASELINE - (GROUND_ROW - TRAIN_TABLET_BOTTOM + 4) * SPRITE_SCALE, 120, 70, 0x7fe0d6,
                 .25f + .12f * sinf(time * 2.2f));
        }
    }
    if (!train_stage || run->train.inside) {
        for (int part = 0; part < EXPERIMENTAL_PARTS; part++) {
            float at;
            if (run->weapon_parts & (1u << part) || !train_part_position(run, part, &at)) continue;
            int cx = (int)lroundf(at - camera);
            if (cx < -200 || cx > VIEW_WIDTH + 200) continue;
            int bottom = run->train.inside ? BASELINE - (GROUND_ROW - TRAIN_CRADLE_TOP) * SPRITE_SCALE
                                           : BASELINE - 3 * SPRITE_SCALE;
            draw_part(r, part, cx, bottom, time);
        }
    }
    if (!train_stage || run->phase != RUN_FIGHTING) return;
    if (run->train.inside) {
        /* The hatch's lamp: red until everything is done, then green. */
        int x = (int)lroundf(train_room_left(run, TRAIN_ROOMS - 1) + TRAIN_EXIT_LAMP_ART * SPRITE_SCALE - camera);
        int y = BASELINE - (GROUND_ROW - 166) * SPRITE_SCALE;
        bool open = train_exit_open(run);
        unsigned lamp = open ? 0x7fe39a : 0xe5523e;
        bool lit = open || fmodf(time, 1.0f) < .6f;
        rect(r, x, y, 2 * SPRITE_SCALE, 4 * SPRITE_SCALE, lit ? lamp : 0x3a1a16, 255);
        if (lit) glow(r, x + SPRITE_SCALE, y + 2 * SPRITE_SCALE, 90, 90, lamp, .7f);
        /* The terminal's screen calls until it has been read. */
        if (!run->train.control_read) {
            int tx = (int)lroundf(train_terminal_x(run) - camera);
            glow(r, tx, BASELINE - (GROUND_ROW - 186) * SPRITE_SCALE, 260, 200, 0xe8aa5a,
                 .25f + .2f * sinf(time * 3.0f));
        }
    }
    float target;
    TrainGoal goal = train_next_goal(run, player, &target);
    int top = 0;
    switch (goal) {
    case TRAIN_GOAL_BOARD: top = BASELINE - 100 * SPRITE_SCALE; break;
    case TRAIN_GOAL_TABLET: top = BASELINE - (GROUND_ROW - TRAIN_TABLET_BOTTOM + 14) * SPRITE_SCALE; break;
    case TRAIN_GOAL_TERMINAL: top = BASELINE - (GROUND_ROW - 151) * SPRITE_SCALE; break;
    case TRAIN_GOAL_EXIT: top = BASELINE - (GROUND_ROW - 130) * SPRITE_SCALE; break;
    default: return; /* Parts carry their own marker; the infected show themselves */
    }
    chevron(r, (int)lroundf(target - camera), top, time, 0xe8c070);
}

/* ---- Over the view -------------------------------------------------------------- */

typedef enum { GLYPH_PART, GLYPH_TERMINAL } Glyph;

static void glyph(SDL_Renderer *r, Glyph kind, int x, int y)
{
    if (kind == GLYPH_PART) {
        for (int k=0;k<4;k++) rect(r,x+3-k,y+1+k,1+2*k,1,0xc19a4c,255);
        for (int k=0;k<3;k++) rect(r,x+1+k,y+5+k,5-2*k,1,0xc19a4c,255);
        rect(r,x+2,y+3,3,3,0x7ff0e6,255);
    } else {
        rect(r,x,y+1,8,6,0x293d41,255);
        rect(r,x+1,y+2,6,4,0xe8aa5a,255);
        rect(r,x+3,y+7,2,1,0x8f9a94,255);
    }
}

static void where(char *out, size_t size, const StageRun *run, const Player *player, float x)
{
    int room=(int)floorf((x-run->train.left)/(TRAIN_ROOM_W*SPRITE_SCALE));
    room=room<0?0:room>=TRAIN_ROOMS?TRAIN_ROOMS-1:room;
    if (fabsf(x-player->x)<60*SPRITE_SCALE) snprintf(out,size,"AQUÍ");
    else snprintf(out,size,"VAGÓN %02d %s",room+1,x>player->x?"→":"←");
}

/* This briefing belongs to the tablet. It never covers the playable scene. */
static void objectives(SDL_Renderer *r, const StageRun *run, const Player *player, int x, int y, int w)
{
    char label[5][48],status[5][40];
    bool done[5]={run->train.tablet,train_parts_aboard(run->weapon_parts)==3,
                  run->train.control_read,train_crew_left(run)==0,run->train.complete};
    float target;
    TrainGoal goal=train_next_goal(run,player,&target);
    int next=goal==TRAIN_GOAL_TABLET?0:goal==TRAIN_GOAL_PART?1:goal==TRAIN_GOAL_TERMINAL?2:
             goal==TRAIN_GOAL_CREW?3:goal==TRAIN_GOAL_EXIT?4:-1;
    snprintf(label[0],sizeof(label[0]),"TABLETA");
    snprintf(label[1],sizeof(label[1]),"PIEZAS %d/3",train_parts_aboard(run->weapon_parts));
    snprintf(label[2],sizeof(label[2]),"ARCHIVO 4");
    snprintf(label[3],sizeof(label[3]),"INFECTADOS %d/%d",run->train.zombie_count-train_crew_left(run),run->train.zombie_count);
    snprintf(label[4],sizeof(label[4]),"ESCOTILLA");
    snprintf(status[0],sizeof(status[0]),done[0]?"MAPA DISPONIBLE":"VAGÓN 01");
    snprintf(status[1],sizeof(status[1]),done[1]?"RECUPERADAS":"BUSCA LAS CUNAS");
    if (!done[1]) {
        float best=1e30f;
        for (int part=0;part<TRAIN_PARTS_ABOARD;part++) {
            float at;
            if (!(run->weapon_parts&(1u<<part)) && train_part_position(run,part,&at) && fabsf(at-player->x)<best) {
                best=fabsf(at-player->x);where(status[1],sizeof(status[1]),run,player,at);
            }
        }
    }
    if (done[2]) snprintf(status[2],sizeof(status[2]),"LECTURA GUARDADA");
    else if (!run->train.tablet) snprintf(status[2],sizeof(status[2]),"REQUIERE TABLETA");
    else where(status[2],sizeof(status[2]),run,player,train_terminal_x(run));
    if (done[3]) snprintf(status[3],sizeof(status[3]),"TREN DESPEJADO");
    else if (goal==TRAIN_GOAL_CREW) where(status[3],sizeof(status[3]),run,player,target);
    else snprintf(status[3],sizeof(status[3]),"REVISA LOS VAGONES");
    snprintf(status[4],sizeof(status[4]),done[4]?"HAS SALIDO DEL TREN":train_exit_open(run)?"LISTA · VAGÓN 15":"COMPLETA LA MISIÓN");
    rect(r,x,y,w,312,0x0c2025,255);
    rect(r,x,y,2,312,0x355b5c,255);
    ui_text(r,"OBJETIVOS",x+14,y+5,2,0xc5d8c2,ANCHOR_NW);
    rect(r,x+12,y+28,w-24,2,0x355b5c,255);
    for (int i=0;i<5;i++) {
        int ry=y+38+i*54;
        unsigned ink=done[i]?0x8baa7b:i==next?0xe8c070:0xa5c5bf;
        if (i==next) { rect(r,x+8,ry-2,w-16,47,0x243d38,255);rect(r,x+8,ry-2,2,47,0xe8c070,255); }
        if (done[i]) ui_icon(r,ICON_CHECK,x+16,ry+3,1);
        else if (i==next) ui_text(r,"→",x+16,ry-1,2,ink,ANCHOR_NW);
        else { rect(r,x+19,ry+5,6,6,0x52716b,255);rect(r,x+21,ry+7,2,2,0x0c2025,255); }
        int scale=ui_text_width(label[i],2)<=w-48?2:1;
        ui_text(r,label[i],x+38,ry,scale,ink,ANCHOR_NW);
        int detail=ui_text_width(status[i],2)<=w-48?2:1;
        ui_text(r,status[i],x+38,ry+23,detail,done[i]?0x6e8d7b:0x799c99,ANCHOR_NW);
    }
}

static void toast_card(SDL_Renderer *r, const StageRun *run, int part)
{
    int x = TRAIN_TOAST_X, y = TRAIN_TOAST_Y, w = TRAIN_TOAST_W, h = TRAIN_TOAST_H;
    char line[48];
    hud_draw_plate(r, x, y, w, h);
    SDL_Rect well = {x + 6, y + 6, 64, 64};
    rect(r, well.x, well.y, well.w, well.h, 0x1b2427, 255);
    color(r, 0x6b5a48, 255);
    SDL_RenderDrawRect(r, &well);
    SDL_Texture *sheet = assets_texture("sprites/terrain/experimental_parts");
    if (sheet) {
        SDL_Rect src = {part * PART_PX, 0, PART_PX, PART_PX};
        SDL_RenderCopy(r, sheet, &src, &well);
    }
    ui_text(r, "¡PIEZA RECUPERADA!", x + 80, y + 4, 2, COLOR_HUD_XP, ANCHOR_NW);
    ui_text(r, train_part_name(part), x + 80, y + 26, 2, COLOR_HUD_TITLE, ANCHOR_NW);
    snprintf(line, sizeof(line), "PROTOTIPO %d/8", train_part_count(run->weapon_parts));
    ui_text(r, line, x + 80, y + 48, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
}

/* ---- The tablet's map (M): bespoke native art and optional briefing -------- */
#define MAP_X 32
#define MAP_Y 18
#define MAP_W 896
#define MAP_H 504
#define MAP_BEZEL 28
#define MAP_COLUMNS 5
#define MAP_ROWS ((TRAIN_ROOMS + MAP_COLUMNS - 1) / MAP_COLUMNS)
#define MAP_CELL_W 96
#define MAP_CELL_H 94
#define MAP_GAP 14
#define MAP_INK 0x8fe8de
#define MAP_DIM 0x335f60
#define MAP_HERE 0xe8c070
#define MAP_TOXIC 0x8fd45a
#define MAP_GRID_W (MAP_COLUMNS*MAP_CELL_W+(MAP_COLUMNS-1)*MAP_GAP)

static const char *map_name(int room)
{
    static const char *const names[]={"ACCESO","PROTOTIPOS","CULTIVOS","CIRUGÍA","ANÁLISIS",
        "CONTENCIÓN","CRIOGENIA","ARCHIVO","DORMITORIO","COMEDOR","ENFERMERÍA","ARMERÍA","RADIO","MÁQUINAS","CONTROL"};
    return room>=0 && room<TRAIN_ROOMS?names[room]:"";
}

static void toxic_mark(SDL_Renderer *r, int x, int y)
{
    for (int k=0;k<4;k++) rect(r,x+4-k,y+k,1+2*k,1,MAP_TOXIC,255);
    for (int k=0;k<4;k++) rect(r,x+1+k,y+4+k,7-2*k,1,MAP_TOXIC,255);
    rect(r,x+3,y+3,3,3,0x183620,255);
}

static void suit_mark(SDL_Renderer *r, int x, int y)
{
    rect(r,x+2,y,4,4,0xd8b34c,255);rect(r,x+3,y+1,2,2,0x51738c,255);
    rect(r,x+1,y+4,6,4,0xd8b34c,255);rect(r,x+2,y+8,2,3,0xa98735,255);rect(r,x+5,y+8,2,3,0xa98735,255);
}

static void map_cell(SDL_Renderer *r, const StageRun *run, const Player *player, int room, int x, int y, float time)
{
    bool now=run->train.inside && room==train_room(run,player->x);
    unsigned edge=now?MAP_HERE:train_room_toxic(room)?0x59864c:MAP_DIM;
    rect(r,x,y,MAP_CELL_W,MAP_CELL_H,edge,255);
    rect(r,x+2,y+2,MAP_CELL_W-4,MAP_CELL_H-4,now?0x243b33:0x102b30,255);
    char num[16];snprintf(num,sizeof(num),"%02d",room+1);
    ui_text(r,num,x+6,y+3,2,now?MAP_HERE:MAP_INK,ANCHOR_NW);
    ui_text(r,map_name(room),x+6,y+23,1,0x91b4ab,ANCHOR_NW);
    SDL_Texture *plans=assets_texture("sprites/ui/train_map_rooms");
    if (plans) {
        SDL_Rect src={room*44,0,44,22},dst={x+4,y+35,88,44};
        SDL_RenderCopy(r,plans,&src,&dst);
    }
    int gx=x+6,gy=y+80;
    for (int part=0;part<TRAIN_PARTS_ABOARD;part++)
        if (train_part_room(part)==room && !(run->weapon_parts&(1u<<part))) { glyph(r,GLYPH_PART,gx,gy);gx+=13; }
    if (room==TRAIN_ROOMS-1 && !run->train.control_read) { glyph(r,GLYPH_TERMINAL,gx,gy);gx+=13; }
    if (room==0) { suit_mark(r,gx,gy);gx+=13; }
    if (train_room_toxic(room)) { toxic_mark(r,gx,gy);gx+=13; }
    int crew=train_crew_in_room(run,room);
    if (crew>0) {
        snprintf(num,sizeof(num),"%d",crew);
        rect(r,x+MAP_CELL_W-25,y+8,4,7,0xc56b53,255);
        ui_text(r,num,x+MAP_CELL_W-15,y+4,1,0xd89b84,ANCHOR_NW);
    }
    if (now) {
        float share=(player->x-train_room_left(run,room))/(TRAIN_ROOM_W*SPRITE_SCALE);
        share=fmaxf(0,fminf(1,share));
        int at=x+8+(int)lroundf(share*(MAP_CELL_W-16));
        rect(r,at-2,y+57,5,5,fmodf(time,.8f)<.55f?0xffe3a3:MAP_HERE,255);
        rect(r,at-1,y+56,3,7,MAP_HERE,255);
    }
}

void train_render_map(SDL_Renderer *r, const StageRun *run, const Player *player, float time)
{
    ui_dim(r,190);
    SDL_Texture *frame=assets_texture("sprites/ui/field_tablet");
    if (frame) { SDL_Rect dst={MAP_X,MAP_Y,MAP_W,MAP_H};SDL_RenderCopy(r,frame,NULL,&dst); }
    else rect(r,MAP_X,MAP_Y,MAP_W,MAP_H,0x10292d,255);
    int x=MAP_X+MAP_BEZEL+16,y=MAP_Y+MAP_BEZEL+10;
    ui_text(r,"VANTRELL · TREN 4-G",x,y,2,MAP_INK,ANCHOR_NW);
    char location[48];
    if (run->train.inside) snprintf(location,sizeof(location),"VAGÓN %02d · %s",train_room(run,player->x)+1,train_room_name(train_room(run,player->x)));
    else snprintf(location,sizeof(location),run->train.complete?"TREN REVISADO":"FUERA DEL TREN");
    ui_text(r,location,MAP_X+MAP_W-MAP_BEZEL-16,y,1,MAP_HERE,ANCHOR_NE);
    int top=y+32;
    for (int room=0;room<TRAIN_ROOMS;room++) {
        int col=room%MAP_COLUMNS,line=room/MAP_COLUMNS;
        int cx=x+col*(MAP_CELL_W+MAP_GAP),cy=top+line*(MAP_CELL_H+MAP_GAP);
        if (col>0) {
            rect(r,cx-MAP_GAP,cy+53,MAP_GAP,4,MAP_DIM,255);
            rect(r,cx-MAP_GAP/2-2,cy+51,4,8,0x517471,255);
        } else if (line>0) {
            int from=x+(MAP_COLUMNS-1)*(MAP_CELL_W+MAP_GAP)+MAP_CELL_W/2;
            int mid=cy-MAP_GAP/2;
            rect(r,from-1,cy-MAP_GAP,3,MAP_GAP/2,MAP_DIM,255);
            rect(r,cx+MAP_CELL_W/2,mid-1,from-cx-MAP_CELL_W/2+2,3,MAP_DIM,255);
            rect(r,cx+MAP_CELL_W/2-1,mid,3,MAP_GAP/2,MAP_DIM,255);
        }
        map_cell(r,run,player,room,cx,cy,time);
    }
    objectives(r,run,player,x+MAP_GRID_W+16,top,256);
    int ly=top+MAP_ROWS*MAP_CELL_H+(MAP_ROWS-1)*MAP_GAP+18,lx=x;
    glyph(r,GLYPH_PART,lx,ly);lx+=13;lx+=ui_text(r,"PIEZA",lx,ly,1,0x8bb6ac,ANCHOR_NW)+16;
    glyph(r,GLYPH_TERMINAL,lx,ly);lx+=13;lx+=ui_text(r,"ARCHIVO 4",lx,ly,1,0x8bb6ac,ANCHOR_NW)+16;
    toxic_mark(r,lx,ly);lx+=13;lx+=ui_text(r,"AIRE TÓXICO",lx,ly,1,0x8bb6ac,ANCHOR_NW)+16;
    suit_mark(r,lx,ly);lx+=13;ui_text(r,"TRAJES",lx,ly,1,0x8bb6ac,ANCHOR_NW);
    int fy=MAP_Y+MAP_H-MAP_BEZEL-20;
    ui_key(r,x,fy-5,"M");ui_text(r,"CERRAR",x+ui_key_width("M")+8,fy,2,MAP_INK,ANCHOR_NW);
    int nx=x+170;ui_key(r,nx,fy-5,"P");ui_text(r,"INVENTARIO",nx+ui_key_width("P")+8,fy,2,MAP_INK,ANCHOR_NW);
    nx=x+414;ui_key(r,nx,fy-5,"ESC");ui_text(r,"VOLVER",nx+ui_key_width("ESC")+8,fy,2,MAP_INK,ANCHOR_NW);
}

/* Only pickup feedback may cover gameplay; the briefing is on the tablet. */
void train_render_status(SDL_Renderer *r, const StageRun *run, const Player *player, int part, float toast)
{
    (void)player;
    if (run->phase==RUN_FIGHTING && toast>0 && part>=0 && part<EXPERIMENTAL_PARTS) toast_card(r,run,part);
}

bool train_render_verify_layout(void)
{
    bool ok=true;
    for (int room=0;room<TRAIN_ROOMS;room++)
        if (ui_text_width(map_name(room),1)>MAP_CELL_W-12) { fprintf(stderr,"MAPA: nombre fuera de celda.\n");ok=false; }
    int top=MAP_Y+MAP_BEZEL+42;
    if (MAP_X+MAP_BEZEL+16+MAP_GRID_W+16+256>MAP_X+MAP_W-MAP_BEZEL ||
        top+312>MAP_Y+MAP_H-MAP_BEZEL-60 || MAP_Y+MAP_H>WINDOW_HEIGHT) {
        fprintf(stderr,"MAPA: objetivos fuera de la tableta.\n");ok=false;
    }
    if (TRAIN_TOAST_Y<HUD_BAND || TRAIN_TOAST_X+TRAIN_TOAST_W>WINDOW_WIDTH-12) {
        fprintf(stderr,"TREN: aviso de pieza fuera de sus límites.\n");ok=false;
    }
    for (int part=0;part<EXPERIMENTAL_PARTS;part++)
        if (80+ui_text_width(train_part_name(part),2)>TRAIN_TOAST_W-8) { fprintf(stderr,"TREN: nombre de pieza ancho.\n");ok=false; }
    return ok;
}
