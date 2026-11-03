#ifndef CONFIG_H
#define CONFIG_H

/* Window */
#define WINDOW_TITLE "Vaquera 2D"
#define WINDOW_WIDTH 960
#define WINDOW_HEIGHT 540

/* Simulation runs at a fixed step; rendering follows vsync. */
#define FIXED_DT (1.0f / 60.0f)
#define MAX_FRAME_TIME 0.25f
/* With vsync, a measured frame time this close to a whole number of steps
 * (or half a step, at 120 Hz) is taken as exact: the display really refreshes
 * evenly, the jitter is only when the loop wakes up. */
#define FRAME_SNAP_TOLERANCE 0.1f /* Fraction of the target */

/* World */
/* The world is laid out in a view VIEW_WIDTH x VIEW_HEIGHT px (its art at
 * SPRITE_SCALE) and drawn at VIEW_SCALE of that: 3 window px per art px,
 * still whole pixels, so she sees a third more of the road. It fills the
 * window's bottom; the band above it is sky, where the HUD sits. */
#define VIEW_WIDTH 1280
#define VIEW_HEIGHT 540
#define VIEW_SCALE 0.75f
#define VIEW_TOP (WINDOW_HEIGHT - (int)(VIEW_HEIGHT * VIEW_SCALE)) /* Window y of the view's top: 135 */
#define BASELINE 470
#define SPRITE_SCALE 4
#define GROUND_ROW 117 /* Art row of the ground line (window y 468); props rest on it */
#define FOG_DRIFT 24.0f /* Window px per second the fog slides on its own (6 art px) */

/* The level is a long strip of chunks whose props are generated from a seed.
 * Only the chunks in view (plus WORLD_LOAD_MARGIN on each side) exist in
 * memory: walking left loads the left ones and drops those left behind on the
 * right, and vice versa. The background layers are images (themes.c). */
#define WORLD_CHUNK_W 480                /* px, half a window */
#define WORLD_CHUNKS 200                 /* 96 000 px, about 100 windows */
#define WORLD_WIDTH ((float)(WORLD_CHUNK_W * WORLD_CHUNKS))
#define WORLD_LOAD_MARGIN 1              /* Chunks loaded past each side of the view */
#define WORLD_CACHE_CHUNKS 8             /* Chunk slots: view (3) + margins */
#define WORLD_SEED 0x7a51e7u             /* Same seed, same landscape */
#define WORLD_MAX_PROPS 8                /* Props per chunk: 2 big ones and the grass */

/* Player sprite sheets: frames in a single row, facing right.
 * Sheet width must be exactly frame width * frame count. */
#define PLAYER_WALK_FRAME_W 42
#define PLAYER_WALK_FRAME_H 67
#define PLAYER_WALK_FRAMES 8
#define PLAYER_WALK_FPS 12.0f /* 5 display frames per art frame at 60 Hz: an even cadence */

#define PLAYER_JUMP_FRAME_W 54
#define PLAYER_JUMP_FRAME_H 82
#define PLAYER_JUMP_FRAMES 8     /* 0-5 follow the arc, 6-7 are the landing */
#define PLAYER_JUMP_AIR_FRAMES 6
#define PLAYER_LAND_FPS 15.0f

#define PLAYER_SHOOT_FRAME_W 81
#define PLAYER_SHOOT_FRAME_H 80
#define PLAYER_SHOOT_FRAMES 8     /* 0-2 draw, 3 aim, 4 fire, 5-6 recoil, 7 holster */
#define PLAYER_SHOOT_AIM_FRAME 3  /* A follow-up shot restarts here, already aimed */
#define PLAYER_SHOOT_FIRE_FRAME 4 /* The bullet leaves on this frame */
#define PLAYER_SHOOT_FPS 16.0f
#define PLAYER_SHOOT_RELOAD_FRAME 6 /* Recoil frame held while the next ball goes in */
/* Seconds from a bullet until the next shot can start. With the aim frame
 * a follow-up fires 1/16 s later: one bullet every 0.445 s. */
#define PLAYER_SHOOT_RELOAD_TIME 0.3825f
#define PLAYER_RELOAD_FRAMES 8 /* A magazine going in (reload sheets), over the gun's reload time */
#define PLAYER_RELOAD_WALK_MULT 0.5f /* Walking while a magazine goes in: half speed */
#define PLAYER_VAULT_SPEED 520.0f  /* Window px per second over a barricade: clears it in one jump */
#define VAULT_REACH 80.0f          /* Window px from where a barricade stops her to vault it */
#define PLAYER_WAIST_ROW 46        /* Walk-frame row where legs start (reloading while walking) */
/* Sitting on a bench (sit sheet, tools/make_sit.py): 12 frames of 72 x 67. */
/* The blow with the gun (V): the melee sheets (tools/make_melee.py). */
#define PLAYER_MELEE_FRAMES 7
#define PLAYER_MELEE_FPS 10.0f
#define PLAYER_MELEE_HIT_FRAME 3  /* The blow lands on this frame */
#define MELEE_COOLDOWN 1.5f       /* Seconds after the blow ends before the next... */
#define HEAT_MELEE_MULT 1.4f      /* ...this much longer in the heat (StageDef.hot)... */
#define COLD_MELEE_MULT 1.3f      /* ...and in the cold (StageDef.cold) */
#define COLD_PACE 0.94f           /* The cold slows her a little */
/* Wet from a river: she dries in this many seconds; by a campfire, faster. */
#define DRY_HOT 8.0f
#define DRY_MILD 11.0f
#define DRY_COLD 15.0f
#define DRY_FIRE 6.0f
/* By a campfire in the heat: fatigue builds up (it wears off at FATIGUE_EASE
 * times the pace away from the fire). Past FATIGUE_SLOW she is slower at
 * everything, past FATIGUE_STROKE a heatstroke blurs the view, at
 * FATIGUE_FAINT she faints and the stage starts over (FAINT_RESTART later). */
#define FATIGUE_SLOW 10.0f
#define FATIGUE_STROKE 15.0f
#define FATIGUE_FAINT 20.0f
#define FATIGUE_EASE 2.0f
#define FATIGUE_PACE 0.8f         /* Her pace, blows and shots once slowed */
#define FAINT_RESTART 3.0f
/* A jug of water (from crates and the wagon, kept till drunk): U drinks it
 * when she isn't bleeding (bleeding, U binds the wound first). Drinking she
 * walks at DRINK_PACE; after, the heat leaves her alone for REFRESH_TIME. */
#define DRINK_TIME 1.2f
#define DRINK_PACE 0.25f
#define REFRESH_TIME 20.0f
#define SUPPLY_WATER 1            /* Jugs in the supply wagon */
#define HYDRATED_PACE 1.08f       /* Hydrated (REFRESH_TIME after a drink): a little quicker */
/* Thirst grows with time (per second: in the heat, mild, cold; none while
 * hydrated) and a drink takes it to 0. Past THIRSTY her mouth is dry, past
 * DEHYDRATED she is slower and her mind starts to go, past HALLUCINATING
 * she sees things (hallucination.c). */
#define THIRST_HOT 1.0f
#define THIRST_MILD 0.5f
#define THIRST_COLD 0.35f
#define THIRSTY 40.0f
#define DEHYDRATED 70.0f
#define HALLUCINATING 100.0f
#define DEHYDRATED_PACE 0.92f
#define PHANTOMS_MAX 4            /* Zombies that aren't there */
#define PHANTOM_EVERY 5.0f        /* Seconds between them */
#define PHANTOM_SPEED 70.0f
#define PHANTOM_REACH 110.0f      /* Window px from her: it was never there */
#define PHANTOM_FADE 0.4f
#define DOUBLE_EVERY 9.0f         /* Seconds between sightings of herself... */
#define DOUBLE_TIME 3.0f          /* ...each this long... */
#define DOUBLE_GAP 380.0f         /* ...this far ahead of her */
#define PLAYER_FAINT_FRAMES 8     /* <id>/faint: swaying, knees giving, toppling, lying (make_faint.py) */
#define PLAYER_FAINT_FRAME_W 80
#define PLAYER_FAINT_FPS 7.0f
#define MELEE_REACH 130.0f        /* Window px past her body's front edge */
#define MELEE_DAMAGE_MULT 0.6f    /* Times her weapon damage (less than a shot)... */
#define MELEE_ARMOR_SHARE 0.5f    /* ...with half the armor in the way */
#define MELEE_PUSH 70.0f          /* Window px a zombie is knocked back */
#define PLAYER_THROW_FRAMES 8      /* The grenade throw, on the shoot template */
#define PLAYER_THROW_FPS 14.0f
#define PLAYER_THROW_RELEASE_FRAME 4 /* The grenade leaves the hand */
#define PLAYER_SIT_FRAME_W 72
#define PLAYER_SIT_ANCHOR_X 35.5f  /* Sat facing the viewer: the body in the frame's middle */
#define PLAYER_SIT_FRAMES 14
#define SIT_DOWN_TIME 0.2f         /* Frame 0, getting down */
#define SIT_RELOAD_TIME 2.0f       /* Frames 4-9, per gun missing a round: it gets full */
#define SIT_BREATH_FPS 1.5f        /* Frames 1-3, sat */
#define SIT_DOZE_TIME 7.0f         /* Seconds sat before she starts nodding off (frames 10-13) */
#define SIT_DOZE_FPS 2.5f

/* Gun smoke (smoke.c): puffs leave the muzzle one after another, rise, drift
 * ahead, grow and fade. Colors are the greys the shoot sheet's smoke used. */
#define SMOKE_PUFFS_PER_SHOT 6      /* The revolver's; each gun sets its own (weapons.c) */
#define SMOKE_MAX_PUFFS 64          /* Enough for the clouds of several shots */
#define SMOKE_PUFF_INTERVAL 0.05f   /* Seconds between puffs of one shot */
#define SMOKE_PUFF_LIFE 0.75f       /* Seconds a puff lasts, +-20% */
#define SMOKE_DRIFT_SPEED 55.0f     /* px/s ahead, slowed by SMOKE_DRAG */
#define SMOKE_RISE_SPEED 45.0f      /* px/s up */
#define SMOKE_DRAG 3.0f             /* Per second: how fast the push dies out */
#define SMOKE_WOBBLE 14.0f          /* px/s of sideways sway */
#define SMOKE_PUFF_START_SIZE 2     /* Art px */
#define SMOKE_PUFF_END_SIZE 6
#define SMOKE_MAX_ALPHA 215

/* Where the bullet's center appears in the fire frame, measured on the art
 * relative to the body's pivot: centered on the barrel (rows 31-34), with the
 * back of the 6 px ball at the muzzle tip (x 64). */
#define PLAYER_MUZZLE_DX 35.5f /* Art px ahead of the body center */
#define PLAYER_MUZZLE_DY 35.0f /* Art px above the ground line */

/* Bullet sheet: 4 frames of 8 x 6 px, a 6 x 6 ball centered in each. */
#define BULLET_FRAME_W 8
#define BULLET_FRAME_H 6
#define BULLET_FRAMES 4
#define BULLET_FPS 12.0f
#define BULLET_SPEED 900.0f /* px per second */
#define BULLET_MAX 16       /* Bullets alive at once */

/* Damage: a weapon of level L deals DAMAGE_BASE * (1 + DAMAGE_LEVEL_GROWTH * (L - 1)),
 * so each level adds 60% of the base. Armor A lets through ARMOR_SCALE / (ARMOR_SCALE + A)
 * of it: 85 armor stops 46%, and no amount of armor makes an enemy immune. */
#define DAMAGE_BASE 20.0f
#define DAMAGE_LEVEL_GROWTH 0.6f
#define ARMOR_SCALE 100.0f

/* Progression (progression.c): the player and the zombies grow by the same
 * rules. At level L, health is base * (1 + DAMAGE_LEVEL_GROWTH * (L - 1)), the
 * same growth as damage, so a fight between equal levels lasts about as long
 * at level 9 as at level 1; armor adds a little per level on top. How hard a
 * stage feels comes from the level gap its zombies have with her (stages.c).
 * tests/test_progression.c plays the campaign and checks it stays winnable. */
#define MAX_LEVEL 50
#define PLAYER_ARMOR_PER_LEVEL 5.0f
#define ZOMBIE_ARMOR_PER_LEVEL 8.0f
/* XP to go from level L to L + 1: XP_CURVE_BASE * L^XP_CURVE_EXP. */
#define XP_CURVE_BASE 120.0f
#define XP_CURVE_EXP 1.5f
/* A kill gives XP_PER_ZOMBIE_LEVEL x the zombie's level, +-XP_GAP_STEP per
 * level it is above or below her (within XP_GAP_MIN..XP_GAP_MAX): weaker
 * zombies are worth less, so replaying easy stages can't skip the curve. */
#define XP_PER_ZOMBIE_LEVEL 11.0f
#define XP_GAP_STEP 0.25f
#define XP_GAP_MIN 0.25f
#define XP_GAP_MAX 1.75f
/* A chest gives CHEST_XP_SHARE of what her level needs, times the stage's
 * complexity, more the further into the mission (x0.75 first .. x1.25 last),
 * with the same level-gap factor; the mission's last chest doubles. */
#define CHEST_XP_SHARE 0.10f
#define CHEST_MISSION_BONUS 2.0f

/* Chest sheet: 6 frames of 72 x 72, closed to open, body on x 15..57 and
 * resting on row 66 (the zombie's template). */
#define CHEST_FRAME_W 72
#define CHEST_FRAME_H 72
#define CHEST_FRAMES 6
#define CHEST_FPS 10.0f
#define CHEST_OPEN_RANGE 110.0f /* Window px between centers: walk up to it to open it */
#define CHEST_STAY_TIME 1.2f    /* Seconds it stays open before fading */
#define CHEST_FADE_TIME 0.5f
/* Sparks bursting out as it opens: 8 frames on the same 72 x 72 template. */
#define CHEST_SPARKS_FRAMES 8
#define CHEST_SPARKS_FPS 12.0f

/* Level badges (tools/make_sprites.py): an inverted pyramid of 17 x 19 art px,
 * drawn at 2 px per art px. The game writes the level in its top band. */
#define BADGE_W 17
#define BADGE_H 19
#define BADGE_SCALE 2
#define BADGE_BAND_TOP 2    /* Rows of the band where the number goes */
#define BADGE_BAND_BOTTOM 9
#define COLOR_BADGE_PLAYER_INK 0xffe7a0
#define COLOR_BADGE_ZOMBIE_INK 0xe8e0d0

/* Zombie sheets: 72 x 72 frames, body centered on x 27.5, boots ending on row 66. */
#define ZOMBIE_FRAME_W 72
#define ZOMBIE_FRAME_H 72
#define ZOMBIE_WALK_FRAMES 8
#define ZOMBIE_WALK_FPS 7.95f /* Its feet keep up with ZOMBIE_SPEED */
#define ZOMBIE_HURT_FRAMES 3     /* 0 recoil with sparks, 1 sparks fade, 2 back to stance */
#define ZOMBIE_HURT_FPS 12.0f
#define ZOMBIE_DEATH_FRAMES 8    /* 0 standing, 1 jolt with sparks, 2-4 knees, 5-6 falls, 7 lying */
#define ZOMBIE_DEATH_FPS 10.0f
#define ZOMBIE_ATTACK_FRAMES 6   /* 0-1 wind up, 2 strike, 3 hold, 4-5 recover */
#define ZOMBIE_ATTACK_FPS 11.0f
#define ZOMBIE_ATTACK_STRIKE_FRAME 2
#define ZOMBIE_ATTACK_BASE 15.0f /* Same formula as the weapon, with this base */
#define ZOMBIE_ATTACK_RANGE 180.0f   /* Claw trail's reach, window px between body centers */
#define ZOMBIE_CLAW_HEIGHT 60.0f     /* Window px over the ground: her feet above this, it misses */
#define ZOMBIE_ATTACK_COOLDOWN 0.72f /* Seconds between the end of one attack and the next */
#define ZOMBIE_STAGGER_COOLDOWN 0.5f /* After a recoil, hits only spark for this long */
#define ZOMBIE_SPEED 63.6f       /* px per second, a slow limp */
#define ZOMBIE_BREATH_TIME 1.6f  /* Seconds of one breath while it waits asleep */
#define ZOMBIE_ROUSE_TIME 0.6f   /* Seconds it jolts awake and lurches before it walks */
#define ZOMBIE_REACH 140.0f      /* Stops this far from the player's center: claw tip on her body */
#define ZOMBIE_HALF_WIDTH 16.0f  /* Hitbox, in art px from the body center */
#define ZOMBIE_HEIGHT 60.0f      /* Hitbox, in art px above the ground line */
#define ZOMBIE_SPAWN_MARGIN 80.0f /* Spawn point's distance from the view's edge */
#define ZOMBIE_CORPSE_TIME 1.5f  /* Seconds the body lies still before fading */
#define ZOMBIE_FADE_TIME 0.6f    /* Seconds the body takes to fade out */
#define ZOMBIE_NEXT_DELAY 1.0f   /* Seconds after the body (or the chest) is gone before the next */
#define ZOMBIE_GROWL_INTERVAL 6.0f /* Seconds between growls while it is alive */

/* Sparks of a bullet on armor: frames 0-1 of hurt.png's burst, cut out. */
#define SPARKS_FRAME_W 20
#define SPARKS_FRAME_H 12
#define SPARKS_FRAMES 2
#define SPARKS_FPS 12.0f

/* Top of her hat above the ground line, in art px: 57 in the walk, shoot and
 * jump sheets alike. Her level tag and reward popups sit above it. */
#define PLAYER_HEAD_HEIGHT 57

/* Half the body's on-screen width, used to keep it inside the world. */
#define PLAYER_HALF_WIDTH (PLAYER_WALK_FRAME_W * SPRITE_SCALE / 2.0f)

#define PLAYER_START_X (WORLD_WIDTH / 2.0f) /* Mid-level: room to walk both ways */
/* Where she stands in the view, from its left edge: the roads lead right, so
 * two thirds of the screen show what is coming. */
#define CAMERA_PLAYER_SHARE 0.32f
/* Whole pixels per 60 Hz step (4 walking, 6 running), so scrolling moves the
 * same amount every frame instead of an uneven 6, 7, 6, 6, 7... */
#define PLAYER_WALK_SPEED 240.0f   /* px per second */
#define PLAYER_RUN_SPEED_MULT 1.5f
#define PLAYER_RUN_ANIM_MULT 1.25f /* 15 fps: 4 display frames per art frame */

/* Health at level 1: the zombie's claw (15) loses a fifth to 25 armor, so she takes 12. */
#define PLAYER_HEALTH 100
#define PLAYER_ARMOR 25.0f
#define PLAYER_HURT_TIME 0.4f       /* Seconds she blinks red after a hit */
#define PLAYER_BLINK_PERIOD 0.05f   /* Seconds per red / normal blink */
#define PLAYER_KNOCKBACK_TIME 0.12f /* Seconds she is pushed away from the hit */
#define PLAYER_KNOCKBACK_SPEED 240.0f

/* Jump arc: peak height in window px and total time in the air. */
#define PLAYER_JUMP_HEIGHT 135.0f
#define PLAYER_JUMP_TIME 0.7f

/* The stage's road (stage_run.c, stages.c): she walks from PLAYER_START_X
 * to a gate StageDef.length ahead, past its zombies' groups and its terrain. */
#define RUN_MAX_ZOMBIES 24
#define RUN_MAX_CHESTS 6
/* XP of a stage's kills and zombie chests is shared out as if it had this
 * many zombies: more zombies make it harder, not a faster climb. */
#define STAGE_XP_ZOMBIES 6.0f
/* A group wakes when even its farthest zombie is this close: they all stand
 * in view first (she sees 870 px ahead), none walks in from off screen. */
#define ROUTE_WAKE_DISTANCE 820.0f
#define ROUTE_GROUP_SPACING 150.0f /* Window px between the zombies of a group */
#define ROUTE_LOCK_MARGIN 260.0f   /* A woken group keeps her from going past its last zombie + this */
/* An ambush (SPOT_AMBUSH): when she reaches its spot, its zombies walk in
 * from off screen, behind her (she sees 410 px back) and, if the road ahead
 * is open, ahead too. */
#define AMBUSH_BEHIND 560.0f
#define AMBUSH_AHEAD 1000.0f
#define AMBUSH_SPACING 120.0f      /* Window px between ambushers on one side */
#define AMBUSH_ROOM 560.0f         /* Window px past the spot she may move while it holds her */
#define ROUTE_PX_PER_METER 48.0f   /* For the distance to the goal in the HUD */
#define ROUTE_QUEUE_STEP 40.0f     /* Zombies queue up by her: each a step behind; two still reach */
#define PLAYER_BODY_HALF_WIDTH 40.0f /* What runs into a barricade: her body, not the frame */

/* Terrain (terrain.c, art from tools/make_terrain.py). */
#define TERRAIN_MAX 96
#define POWER_LEVEL 3             /* Each character's level-3 power: dual pistols, grenades */
#define GRENADE_SPEED_X 430.0f    /* Window px/s ahead when thrown */
#define GRENADE_SPEED_Y 560.0f    /* ...and up */
#define GRENADE_GRAVITY 1500.0f
#define GRENADE_BOUNCE 0.35f      /* Speed kept off the ground or a wall */
#define GRENADE_FUSE 1.5f         /* Seconds from the throw to the blast */
#define GRENADE_RADIUS 260.0f     /* Window px to a body's edge: the blast reaches it */
#define GRENADE_DAMAGE_MULT 3.0f  /* Times her weapon damage, armor at BARREL_ARMOR_SHARE */
#define GRENADE_SELF_MULT 1.0f    /* Claws of the stage's zombies on her, if she's caught in it */
#define POWER_COOLDOWN 15.0f      /* Seconds between uses of a level-3 power (F) */
#define RICOCHET_LOSS 0.55f       /* A ricochet's second hit: 45% less damage... */
#define RICOCHET_KILL_BONUS 1.30f /* ...or 30% more if the first target died */
#define RICOCHET_TINT 0xffd060    /* Its bullets glow gold */
#define GRENADE_FRAME 8           /* weapons/grenade: 4 frames tumbling */
#define HOUSE_FRAME_W 80          /* Buildings off the road, behind it (props/houses) */
#define HOUSE_FRAME_H 64
#define HOUSE_FRAMES 9           /* Five houses, then church, sheriff, smithy, stable */
#define HOUSE_SCALE 3             /* Smaller than the props: further away */
#define HOUSE_PARALLAX 0.8f       /* ...and slower */
#define HOUSE_SPACING 700.0f      /* A slot for a house every this many px of their strip */
#define BARRICADE_FRAME_W 68
#define BARRICADE_FRAME_H 26
#define BARRICADE_TOP 100.0f      /* Window px: above the claw, under her jump's peak */
#define BARRICADE_STRIKES 4       /* Claw strikes that wreck it */
#define BARRICADE_KINDS 4         /* Crates, sandbags, logs, a steel barrier (Piece.variant) */
#define BARRICADE_CLAW_GAP 36.0f  /* A zombie clawing it stands this far from its edge */
#define WALL_FRAME_W 44           /* The tall palisade: her height, no jumping it */
#define WALL_FRAME_H 72
#define WALL_RUINS_W 180          /* The ruined house round a palisade, drawn behind it */
#define WALL_RUINS_H 84
#define FACADE_W 180              /* A wall that is a building's front: church, sheriff... */
#define FACADE_H 128
#define FACADE_KINDS 4
#define DOOR_FRAME_W 44           /* ...its barred door, as wide as the palisade */
#define DOOR_FRAME_H 64
#define WALL_STRIKES 14           /* Claws take a long while; a blast takes a moment */
#define WALL_USE_RANGE 70.0f      /* Window px from its edge to light a charge on it */
#define CHARGE_FUSE 2.5f          /* Seconds from lighting to the blast: time to step back */
#define CHARGE_FRAME_W 14
#define CHARGE_FRAME_H 20
#define DYNAMITE_FRAME_W 24
#define DYNAMITE_FRAME_H 18
#define DYNAMITE_PER_BOX 1
#define PICKUP_RANGE 80.0f        /* Window px from a box's center: walk over it */
#define BARREL_FRAME_W 26
#define BARREL_FRAME_H 36
#define BARREL_RADIUS 320.0f      /* Window px from the barrel to a body's edge: the blast reaches it */
#define BARREL_CHAIN_RADIUS 260.0f /* ...and sets off barrels this close */
#define BARREL_SHOT_MARGIN 16.0f  /* Window px over its lid a bullet still hits it */
#define BLAST_FIRE_SPREAD 120.0f  /* Burning patches left either side of a blast, this far apart */
#define BLAST_FIRE_TIME 2.0f      /* Seconds they burn (each a little more or less) */
#define WALL_BARREL_GAP 170.0f    /* A barrel set against a wall, this far before it */
#define BARREL_DAMAGE_MULT 4.0f   /* Times her weapon damage, so it grows with upgrades */
#define BARREL_ARMOR_SHARE 0.5f   /* Armor counts half against a blast */
#define BARREL_SELF_MULT 2.0f     /* Her own blast hurts like this many claws of the stage's zombies */
#define SUPPLY_FRAME_W 100
#define SUPPLY_FRAME_H 56
#define SUPPLY_RANGE 160.0f       /* Window px from its center: walk up to take it */
#define SUPPLY_HEAL_SHARE 0.35f   /* Of her max health */
#define SUPPLY_DYNAMITE_MEDIUM 20000.0f /* Roads longer than this: 2 charges in the wagon */
#define SUPPLY_DYNAMITE_LONG 28000.0f   /* ...and than this: 3 */
#define GOAL_FRAME_W 108
#define GOAL_FRAME_H 96
#define CRATE_FRAME_W 32          /* A loose crate: 3 shots to break, loot inside (stencilled on it) */
#define CRATE_FRAME_H 28
#define CRATE_HITS 3
#define CRATE_SPACING 140.0f      /* Window px between crates of one spot */
#define TRAP_SPACING 220.0f
/* Water on the road. A river (terrain/river: its top rows over the ground
 * line, the rest down to the bottom of the view) slows whoever wades it;
 * its surface (river_front) is drawn again over their feet. A puddle only
 * splashes and ripples. */
#define RIVER_FRAME_W 120
#define RIVER_FRAME_H 22
#define RIVER_SINK 18             /* Art rows under the ground line */
#define RIVER_FRONT_H 3           /* Ankle deep */
#define RIVER_FPS 8.0f
#define RIVER_CLEARANCE 1200.0f   /* 25 m at least between a river and a building or ruin */
#define RIVER_SLOW 0.5f           /* Pace in the water, hers and the zombies'... */
#define RIVER_WITH 1.2f           /* ...times this going with the current (it flows right)... */
#define RIVER_AGAINST 0.8f        /* ...or this against it */
#define WIND_WITH 1.15f           /* Pace with the wind at your back (it blows right)... */
#define WIND_AGAINST 0.85f        /* ...and into it */
#define OMEN_CHANCE 38            /* Percent of ambushes she gets a bad feeling about... */
#define OMEN_RANGE 1800.0f        /* ...this far before it */
#define BANDAGE_TIME 1.5f         /* Seconds holding U to stop the bleeding... */
#define BANDAGE_WALK 0.5f         /* ...walking at this pace meanwhile */
#define PLAYER_CARE_FRAMES 6      /* <id>/drink and <id>/bandage: the shoot template */
#define BANDAGE_SHOW 2.5f         /* Seconds the done bandage stays on her leg */
#define SIGN_FRAME_W 22           /* terrain/sign: a warning sign by a trap */
#define SIGN_FRAME_H 30
#define SIGN_CHANCE 25            /* Percent of traps with one */
#define SIGN_GAP 200.0f           /* Window px before the trap */
#define SIGN_WARN_RANGE 360.0f    /* Its warning shows this far before it */
#define PUDDLE_FRAME_W 36
#define PUDDLE_FRAME_H 5
#define PUDDLE_SINK 4
#define PUDDLE_SPACING 320.0f
#define RIPPLE_TIME 0.5f          /* Seconds a puddle's rings spread */
#define SPLASH_FRAME_W 20         /* effects/splash: 5 frames */
#define SPLASH_FRAME_H 12
#define SPLASH_FRAMES 5
#define SPLASH_FPS 14.0f
#define SPLASH_EVERY 0.25f        /* Seconds between splashes of a walker in water */
/* Weather (weather.c). */
#define WEATHER_DROPS 160
#define WEATHER_DUST 16
#define WEATHER_SPLASHES 24
#define RAIN_SPEED 950.0f         /* View px per second down */
#define RAIN_SLANT 0.6f           /* Of the wind, sideways */
#define WIND_SPEED 520.0f
#define TUMBLE_EVERY 7.0f         /* Seconds between tumbleweeds, about */
#define TUMBLE_FRAME 14           /* effects/tumbleweed: 4 frames */

/* Crows on the road (crows.c): effects/crow, 6 frames. */
#define CROW_FRAME_W 16
#define CROW_FRAME_H 12
#define CROWS_MAX 48
#define CROW_FLOCK_EVERY 2600.0f  /* Window px between flocks, about */
#define CROW_SCARE_RANGE 330.0f   /* She walks this near, they go (standing: 40 %) */
#define CROW_SHOT_RANGE 900.0f    /* A shot this far away scares them... */
#define CROW_BLAST_RANGE 1800.0f  /* ...a blast this far */
#define CROW_FLY_SPEED 240.0f     /* Px per second away, at least */
#define CROW_CLIMB 260.0f
#define CROW_FLAP_FPS 14.0f
#define CROW_GONE_HEIGHT 900.0f
#define CROW_FALL_GRAVITY 1400.0f /* A dead one drops */
#define CROW_CORPSE_TIME 4.0f     /* Seconds it lies on the road... */
#define CROW_FADE_TIME 0.8f       /* ...then fades */
#define CROW_FRAMES 8
/* Traps that hang their catch up (CatchKind): a net (a bag up in the air)
 * and a snare (by one foot, head down, from a sapling). She gets out with
 * blows (V); a zombie hangs a while and drops. */
#define NET_FRAME_W 40
#define NET_FRAME_H 30
#define NET_BAG_W 44              /* effects/net_bag: 2 sway frames, then 2 closing */
#define NET_BAG_H 66
#define NET_LIFT 110.0f           /* Window px her feet go up */
#define NET_BLOWS 3               /* Blows to cut her way out */
#define NET_HOLD 4.0f             /* Seconds a zombie hangs in it */
#define SNARE_FRAME_W 48
#define SNARE_FRAME_H 64
#define SNARE_TIP_X 41            /* Art px in its frame: the sprung sapling's tip */
#define SNARE_TIP_Y 4
#define SNARE_LIFT 70.0f          /* Window px her head hangs over the ground */
#define SNARE_BLOWS 2
#define SNARE_HOLD 5.0f
#define CATCH_RISE_TIME 0.25f     /* Seconds the trap takes to haul its catch up */
#define CATCH_SHAKE_TIME 0.2f     /* A blow at the ropes: her strike frame this long */
#define SPRING_TIME 0.18f         /* Seconds a trap's springing frame shows */
/* A spike plate: stepped on, its spikes come up a moment later and stay out
 * a while, then sink back and it can go again. */
#define SPIKES_FRAME_W 32
#define SPIKES_FRAME_H 16
#define SPIKES_DELAY 0.35f        /* Seconds from the step to the spikes */
#define SPIKES_OUT 0.8f           /* Seconds they stay out */
#define SPIKES_REARM 1.5f         /* Seconds sunk before it can go again */
#define SPIKES_TOP 60.0f          /* Window px: higher in a jump, she clears them */
#define SPIKES_SELF_MULT 1.2f     /* Claws of the stage's zombies on her (plus bleeding) */
#define SPIKES_DAMAGE_MULT 2.5f   /* Times her weapon damage on a zombie */
/* Barbed wire across the road: it doesn't stop her, it tears her (bleeding,
 * limping) while she is in it below WIRE_TOP. Shots or blows cut it. */
#define WIRE_FRAME_W 80
#define WIRE_FRAME_H 22
#define WIRE_HITS 4               /* Shots that cut it */
#define WIRE_MELEE_HITS 2         /* What one blow counts for */
#define WIRE_TOP 70.0f            /* Window px over the ground: higher, she clears it */
#define WIRE_BITE_EVERY 0.8f      /* Seconds between bites while she is in it */
#define WIRE_SELF_MULT 0.5f       /* Claws of the stage's zombies per bite */
#define WIRE_WARN_RANGE 420.0f    /* Window px: the prompt tells her what to do */
#define LAMP_SPACING 320.0f
#define COFFIN_SPACING 130.0f
#define CRATE_HINT_RANGE 700.0f   /* Window px: the first crate of the first stages, a hint */
#define GOLD_CRATE 10              /* Gold in a crate on stage 1-1... */
#define GOLD_CRATE_PER_STAGE 5     /* ...and this much more each stage after */
#define GOLD_CHEST 5               /* Gold in a zombie's chest; the mission's: GOLD_MISSION */
#define GOLD_MISSION 25
#define LOOT_GOLD_SHARE 0.5f      /* A crate's gold: this share of a chest's XP */
#define BOTTLES_XP_SHARE 0.4f     /* All three bottles: this share of a chest's XP */
#define LOOT_AMMO_CHANCE 30       /* Percent of crates: the gun in hand's magazine full */
#define LOOT_HEALTH_CHANCE 25     /* ...health (LOOT_HEALTH_SHARE of her max) */
#define LOOT_DYNAMITE_CHANCE 15   /* ...a charge of dynamite... */
#define LOOT_WATER_CHANCE 15      /* ...a jug of water; the rest, gold (XP) */
#define LOOT_HEALTH_SHARE 0.2f
#define BOTTLES_FRAME_W 36        /* Three bottles on a fence rail: frames with 3, 2, 1, 0 left */
#define BOTTLES_FRAME_H 22
#define BOTTLE_COUNT 3
#define TRAP_FRAME_W 32           /* A bear trap: open, snapping, shut */
#define TRAP_FRAME_H 12
#define TRAP_REACH 60.0f          /* Window px from its center: a foot on it snaps it */
#define TRAP_HOLD 3.0f            /* Seconds a zombie stays caught */
#define TRAP_DAMAGE_MULT 2.0f     /* Times her weapon damage to a zombie; her: TRAP_SELF_MULT claws */
#define TRAP_SELF_MULT 1.5f
#define BLEED_TIME 5.0f           /* Stepping in a trap: seconds she bleeds... */
#define BLEED_TICK 1.0f           /* ...losing health this often... */
#define BLEED_SHARE 0.2f          /* ...this many claws of the stage's zombies each time (armor won't stop it) */
#define SLOW_TIME 4.0f            /* ...and seconds she limps */
#define SLOW_MULT 0.55f           /* Her pace while limping */
#define BLOOD_DROPS 64            /* Her trail of blood on the road */
#define BLOOD_EVERY 0.12f         /* Seconds between drops while she bleeds */
#define BLOOD_LIFE 8.0f           /* Seconds a drop takes to dry away */
#define COFFIN_FRAME_W 28         /* Upright coffin: shut, burst open; by day, by night */
#define COFFIN_FRAME_H 60
#define COFFIN_CHANCE_DAY 40      /* Percent of a coffin spot's zombies in a coffin, by day... */
#define COFFIN_CHANCE_NIGHT 85    /* ...and by night (ThemeDef.night) */
#define COFFIN_HITS 2             /* Shots that burst it open early */
#define COFFIN_RANGE 340.0f       /* Window px: she comes this near, it bursts open */
#define LAMP_FRAME_W 14           /* Oil lamp on a post: lit, post without its lamp */
#define LAMP_FRAME_H 56
#define FIRE_FRAME_W 32           /* Burning oil on the ground */
#define FIRE_FRAME_H 24
#define FIRE_FRAMES 4
#define FIRE_FPS 10.0f
#define FIRE_TIME 5.0f            /* Seconds a fallen lamp's oil burns */
#define FIRE_REACH 72.0f          /* Window px from its center: in the flames */
#define FIRE_TICK 0.5f            /* Seconds between burns */
#define FIRE_DAMAGE_MULT 0.6f     /* Times her weapon damage per burn, a third of the armor counting */
#define FIRE_SELF_MULT 0.5f       /* Claws of the stage's zombies per burn on her */
#define BENCH_FRAME_W 76           /* A bench to rest on, from the front: its seat at a sitter's lap */
#define BENCH_FRAME_H 32
#define BENCH_RANGE 90.0f          /* Window px from its center: E sits her on it */
#define BENCH_HEAL_MIN 5           /* Health the first sit gives, a fixed roll per bench */
#define BENCH_HEAL_MAX 15
#define CAMPFIRE_FRAME_W 48        /* A campfire to rest by */
#define CAMPFIRE_FRAME_H 44
#define CAMPFIRE_FRAMES 4         /* Per look: the fire alone, then with a pot over it */
#define CAMPFIRE_RANGE 140.0f      /* Window px from its center: warm enough to heal */
#define CAMPFIRE_HEAL 1.5f         /* Health per CAMPFIRE_HEAL_TIME by the fire */
#define CAMPFIRE_HEAL_TIME 3.0f
#define REST_GAP 280.0f            /* A campfire this far past its bench */
#define HEAL_FRAME_W 64            /* The green aura round a healed body and a + over it */
#define HEAL_FRAME_H 96
#define HEAL_GLOW_TIME 2.0f        /* Seconds she glows green after a heal */
#define HEAL_FRAMES 12
#define HEAL_FPS 8.0f
#define GLOW_SIZE 32               /* The light round a flame (effects/glow), stretched */
#define LAMP_LIGHT 300.0f          /* Window px across the light of a lamp */
#define FIRE_LIGHT 380.0f          /* ...of burning oil, a campfire */
#define SMOKE_EVERY 0.35f          /* Seconds between puffs off a fire */
#define EXPLOSION_FRAME_W 72
#define EXPLOSION_FRAME_H 72
#define EXPLOSION_FRAMES 8
#define EXPLOSION_FPS 14.0f

/* The interface's pixel art (game/ui.c) is drawn at this scale: a 24 px
 * board corner is 72 window px. Its text uses the pixel font at 2-8. */
#define UI_SCALE 3

/* Colors (0xRRGGBB) */
#define COLOR_BACKGROUND 0x202229
#define COLOR_SMOKE_FRESH 0xaaa596
#define COLOR_SMOKE_OLD 0x6c6c67

#define COLOR_HEALTH_BACK 0x14151a
#define COLOR_HEALTH_FILL 0xb8402c
#define COLOR_HEALTH_ARMOR 0x6c7486
#define COLOR_HUD_DANGER 0xe0705a

#define COLOR_HUD_TITLE 0xf0d3a1
#define COLOR_HUD_PRIMARY 0xc5bcc1
#define COLOR_HUD_SECONDARY 0x92959d
#define COLOR_HUD_FOOTER 0x9c8a7c
#define COLOR_HUD_LEVEL 0xf0d3a1  /* Level tags above heads */
#define COLOR_HUD_ENEMY 0xe0a090
#define COLOR_HUD_XP 0x7fb069
#define COLOR_HUD_LOCKED 0x5c5a63
#define COLOR_MENU_SELECTED 0x2e2b33

/* Audio: 8-bit effects from assets/sounds (regenerate with tools/make_sfx.py). */
#define AUDIO_RATE 44100
#define AUDIO_BUFFER 512   /* Samples per callback: small, so shots sound on time */
#define AUDIO_CHANNELS 16  /* Effects that can overlap */
#define SFX_VOLUME 60      /* 0-128 (MIX_MAX_VOLUME): every sound, before the volume menu */
#define AUDIO_GROUPS 4     /* Volume groups (audio_play_in): see SoundGroup in settings.h */

#endif
