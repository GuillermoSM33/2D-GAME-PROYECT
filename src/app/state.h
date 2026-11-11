#ifndef APP_STATE_H
#define APP_STATE_H

#include "config.h"
#include "game/almanac.h"
#include "game/bats.h"
#include "game/characters.h"
#include "game/crows.h"
#include "game/hallucination.h"
#include "game/player.h"
#include "game/settings.h"
#include "game/smoke.h"
#include "game/stage_run.h"
#include "game/weather.h"
#include "game/world.h"

/* What the pause shows: its list, or the volume or controls screen opened from it. */
typedef enum { PAUSE_VIEW_LIST, PAUSE_VIEW_VOLUME, PAUSE_VIEW_CONTROLS } PauseView;

#define APP_PROFILE_CAPACITY 8

/* Persistent progress for each character. */
typedef struct {
    Progress progress;
    StageRecord record;
    Almanac almanac;
    Inventory inventory;
} Profile;

/* Everything one play of a stage uses, reset when it starts. */
typedef struct {
    const CharacterDef *character;
    int weapon_slot; /* Which of the character's guns is in hand */
    bool single_fire; /* K: guns with a single mode fire one round per click */
    WeaponId guns[CHARACTER_MAX_WEAPONS]; /* Its guns at its level (a power may change one) */
    bool duals_out;  /* Its power's second pistol in hand (Q takes it out and away) */
    float power_cooldown; /* Seconds until F works again */
    bool ricochet_armed;  /* The next shot's bullets glance on to a second target */
    bool ricochet_fired;  /* ...and it has gone: her hands part when the shot ends */
    int rounds[CHARACTER_MAX_WEAPONS]; /* Shots left in each gun's magazine while put away */
    Player player;
    Bullets bullets;
    Effects effects;
    Smoke smoke;
    StageRun run; /* The road: its zombies, terrain and chests */
    AlmanacEncounter encounter;
    World world;
    float prev_zombie_x[RUN_MAX_ZOMBIES]; /* Before the last step, to draw in between */
    float smoke_timer; /* Seconds until fires puff smoke again */
    Crows crows;
    Bats bats; /* At night, along the road */
    float bat_chirp_wait; /* Occasional calls, separate from fleeing or being hit */
    unsigned bat_chirp_count;
    float faint_timer; /* Seconds since she fainted: the stage starts over at FAINT_RESTART */
    WeatherState weather;
    Hallucination visions; /* What her thirst makes her see */
    float splash_timer; /* Seconds until the walkers in water splash again */
    int footstep_phase;       /* Half of the walk cycle her feet are on, -1 when not walking */
    unsigned footstep_count;  /* Steps taken: left and right feet sound apart */
    float thunder_wait; /* Delay between lightning and its thunder; -1 = none */
    bool lightning_warning; /* A nearby bolt's warning is playing */
    /* Her trail of blood while she bleeds: drops on the road drying away. */
    float blood_x[BLOOD_DROPS], blood_age[BLOOD_DROPS];
    int blood_next;
    float blood_timer;
    /* Her progress when the stage began: a retry or leaving before clearing
     * it puts this back, so replaying a stage can't farm its XP. */
    Progress progress_at_start;
    Inventory inventory_at_start;
    bool paused;     /* Esc: the pause menu, the stage frozen behind it */
    bool music_on;   /* Its track still playing, not yet faded by the ending */
    ListMenu pause_menu;
    PauseView pause_view;
    bool request_almanac;
    bool request_casefile;  /* The pause's EXPEDIENTE */
    int clues_now[3];       /* Clues this step turned up (STAGE_CLUES), for the caller to keep */
    int clue_count;
    int clue_toast;         /* The clue the HUD is announcing, or -1 */
    float clue_toast_time;  /* Seconds left of it */
    bool flashlight;
    float flashlight_since; /* Seconds since its switch was flipped */
    bool flashlight_click_pending; /* Wait until the raising animation reaches the switch */
} StagePlay;

#endif
