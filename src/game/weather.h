#ifndef GAME_WEATHER_H
#define GAME_WEATHER_H

#include <stdbool.h>

#include "config.h"

/* A stage's weather (StageDef.weather): scenery over the view, no effect on
 * the fight. Rain falls slanted and splashes on the road; wind blows dust
 * and leaves across and now and then rolls a tumbleweed through; a storm is
 * both, harder, with lightning. No SDL: weather.c moves the particles, the
 * weather_render.c draws them across the full window, behind the HUD. */
typedef enum {
    WEATHER_CLEAR,
    WEATHER_WIND,
    WEATHER_RAIN,
    WEATHER_STORM
} Weather;

typedef struct {
    float x, y;  /* World x, view y (negative y also covers the sky above the view) */
    float speed; /* Its own pace, times the weather's */
    bool leaf;   /* Wind: a leaf (bigger, fluttering) instead of dust... */
    bool streak; /* ...or a gust line, faster and straight */
} WeatherBit;

typedef struct {
    Weather kind;
    WeatherBit drops[WEATHER_DROPS]; /* Rain */
    WeatherBit dust[WEATHER_DUST];   /* Wind */
    float splash_x[WEATHER_SPLASHES], splash_age[WEATHER_SPLASHES]; /* Drops hitting the road */
    int splash_next;
    bool paper;                      /* In a town: a newspaper blows through instead (the stage sets it) */
    bool tumbling;                   /* A tumbleweed rolling through... */
    float tumble_x, tumble_height, tumble_vy, tumble_time;
    float tumble_wait;               /* ...or seconds until the next */
    float flash;                     /* Lightning: 1 at the strike, fading */
    float flash_wait;                /* Seconds until the next */
    unsigned seed;
} WeatherState;

/* Starts kind over the view at camera_x (its left edge, world px). */
void weather_start(WeatherState *weather, Weather kind, float camera_x);

void weather_update(WeatherState *weather, float camera_x, float dt);

bool weather_rains(const WeatherState *weather);
bool weather_blows(const WeatherState *weather);

/* Px per second the wind pushes things right (0 without wind). */
float weather_wind(const WeatherState *weather);

/* World/view y corresponding to the window's top. Rain must start above this
 * negative height, so it also covers the sky band above the world viewport. */
float weather_view_top(void);

#endif
