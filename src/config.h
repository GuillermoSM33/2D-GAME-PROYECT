#ifndef CONFIG_H
#define CONFIG_H

/* Window */
#define WINDOW_TITLE "Vaquera 2D  |  Demo de caminata"
#define WINDOW_WIDTH 960
#define WINDOW_HEIGHT 540

/* Simulation runs at a fixed step; rendering follows vsync. */
#define FIXED_DT (1.0f / 60.0f)
#define MAX_FRAME_TIME 0.25f

/* World */
#define BASELINE 470
#define SPRITE_SCALE 4

/* Player sprite sheets: frames in a single row, facing right.
 * Sheet width must be exactly frame width * frame count. */
#define PLAYER_WALK_FRAME_W 42
#define PLAYER_WALK_FRAME_H 67
#define PLAYER_WALK_FRAMES 8
#define PLAYER_WALK_FPS 9.0f

#define PLAYER_JUMP_FRAME_W 54
#define PLAYER_JUMP_FRAME_H 82
#define PLAYER_JUMP_FRAMES 8     /* 0-5 follow the arc, 6-7 are the landing */
#define PLAYER_JUMP_AIR_FRAMES 6
#define PLAYER_LAND_FPS 15.0f

#define PLAYER_SHOOT_FRAME_W 81
#define PLAYER_SHOOT_FRAME_H 80
#define PLAYER_SHOOT_FRAMES 8     /* 0-2 draw, 3 aim, 4 fire, 5-6 smoke, 7 holster */
#define PLAYER_SHOOT_AIM_FRAME 3  /* A follow-up shot restarts here, already aimed */
#define PLAYER_SHOOT_FIRE_FRAME 4 /* The bullet leaves on this frame */
#define PLAYER_SHOOT_FPS 16.0f

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
#define WEAPON_LEVEL 1

/* Zombie sheets: 72 x 72 frames, body centered on x 27.5, boots ending on row 66. */
#define ZOMBIE_FRAME_W 72
#define ZOMBIE_FRAME_H 72
#define ZOMBIE_WALK_FRAMES 8
#define ZOMBIE_WALK_FPS 6.0f
#define ZOMBIE_HURT_FRAMES 3     /* 0 recoil with sparks, 1 sparks fade, 2 back to stance */
#define ZOMBIE_HURT_FPS 12.0f
#define ZOMBIE_DEATH_FRAMES 8    /* 0 standing, 1 jolt with sparks, 2-4 knees, 5-6 falls, 7 lying */
#define ZOMBIE_DEATH_FPS 10.0f
#define ZOMBIE_ATTACK_FRAMES 6   /* 0-1 wind up, 2 strike, 3 hold, 4-5 recover */
#define ZOMBIE_ATTACK_FPS 10.0f
#define ZOMBIE_ATTACK_STRIKE_FRAME 2
#define ZOMBIE_ATTACK_BASE 15.0f /* Same formula as the weapon, with this base */
#define ZOMBIE_ATTACK_LEVEL 1
#define ZOMBIE_ATTACK_RANGE 180.0f   /* Claw trail's reach, window px between body centers */
#define ZOMBIE_ATTACK_COOLDOWN 0.8f  /* Seconds between the end of one attack and the next */
#define ZOMBIE_STAGGER_COOLDOWN 0.5f /* After a recoil, hits only spark for this long */
#define ZOMBIE_SPEED 42.0f       /* px per second, a slow limp */
#define ZOMBIE_REACH 140.0f      /* Stops this far from the player's center: claw tip on her body */
#define ZOMBIE_HALF_WIDTH 16.0f  /* Hitbox, in art px from the body center */
#define ZOMBIE_HEIGHT 60.0f      /* Hitbox, in art px above the ground line */
#define ZOMBIE_SPAWN_MARGIN 80.0f /* Spawn point's distance from the window edge */
#define ZOMBIE_CORPSE_TIME 1.5f  /* Seconds the body lies still before fading */
#define ZOMBIE_FADE_TIME 0.6f    /* Seconds the body takes to fade out */
#define ZOMBIE_RESPAWN_DELAY 1.5f /* Seconds after fading before the next one */

/* Sparks of a bullet on armor: frames 0-1 of hurt.png's burst, cut out. */
#define SPARKS_FRAME_W 20
#define SPARKS_FRAME_H 12
#define SPARKS_FRAMES 2
#define SPARKS_FPS 12.0f

/* Half the body's on-screen width, used to keep it inside the window. */
#define PLAYER_HALF_WIDTH (PLAYER_WALK_FRAME_W * SPRITE_SCALE / 2.0f)

#define PLAYER_START_X (WINDOW_WIDTH * 0.25f)
#define PLAYER_WALK_SPEED 198.0f   /* px per second */
#define PLAYER_RUN_SPEED_MULT 1.55f
#define PLAYER_RUN_ANIM_MULT 1.35f

/* Health: the zombie's claw (15) loses a fifth to 25 armor, so she takes 12. */
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
#define COLOR_SKY_BAND 0x26262b
#define COLOR_HILLS 0x24232a
#define COLOR_GROUND_LINE 0xb78d60
#define COLOR_GROUND 0x28262a
#define COLOR_GROUND_STRIPE 0x3a3434
#define COLOR_GROUND_STONES 0x494038

#define COLOR_HEALTH_BACK 0x14151a
#define COLOR_HEALTH_FILL 0xb8402c
#define COLOR_HEALTH_ARMOR 0x6c7486
#define COLOR_HUD_DANGER 0xe0705a

#define COLOR_HUD_TITLE 0xf0d3a1
#define COLOR_HUD_PRIMARY 0xc5bcc1
#define COLOR_HUD_SECONDARY 0x92959d
#define COLOR_HUD_FOOTER 0x9c8a7c

#endif
