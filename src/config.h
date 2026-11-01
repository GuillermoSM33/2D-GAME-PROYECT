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

/* Gun smoke (smoke.c): puffs leave the muzzle one after another, rise, drift
 * ahead, grow and fade. Colors are the greys the shoot sheet's smoke used. */
#define SMOKE_PUFFS_PER_SHOT 6
#define SMOKE_MAX_PUFFS 24          /* Enough for the clouds of several shots */
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
 * of it: 80 armor stops 44%, and no amount of armor makes an enemy immune. */
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
#define XP_PER_ZOMBIE_LEVEL 25.0f
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
#define ZOMBIE_WALK_FPS 7.5f  /* 8 display frames per art frame at 60 Hz */
#define ZOMBIE_HURT_FRAMES 3     /* 0 recoil with sparks, 1 sparks fade, 2 back to stance */
#define ZOMBIE_HURT_FPS 12.0f
#define ZOMBIE_DEATH_FRAMES 8    /* 0 standing, 1 jolt with sparks, 2-4 knees, 5-6 falls, 7 lying */
#define ZOMBIE_DEATH_FPS 10.0f
#define ZOMBIE_ATTACK_FRAMES 6   /* 0-1 wind up, 2 strike, 3 hold, 4-5 recover */
#define ZOMBIE_ATTACK_FPS 10.0f
#define ZOMBIE_ATTACK_STRIKE_FRAME 2
#define ZOMBIE_ATTACK_BASE 15.0f /* Same formula as the weapon, with this base */
#define ZOMBIE_ATTACK_RANGE 180.0f   /* Claw trail's reach, window px between body centers */
#define ZOMBIE_ATTACK_COOLDOWN 0.8f  /* Seconds between the end of one attack and the next */
#define ZOMBIE_STAGGER_COOLDOWN 0.5f /* After a recoil, hits only spark for this long */
#define ZOMBIE_SPEED 60.0f       /* px per second, a slow limp: exactly 1 px per step */
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
#define PLAYER_JUMP_HEIGHT 96.0f
#define PLAYER_JUMP_TIME 0.6f

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
#define SFX_VOLUME 60      /* 0-128 (MIX_MAX_VOLUME) */

#endif
