#include "game/weather.h"

#include <math.h>
#include <string.h>

/* 0..1, from the state's own generator: the same weather every run. */
static float roll(WeatherState *w)
{
    w->seed = w->seed * 1664525u + 1013904223u;
    return (float)(w->seed >> 8) / 16777216.0f;
}

bool weather_rains(const WeatherState *weather)
{
    return weather->kind == WEATHER_RAIN || weather->kind == WEATHER_STORM;
}

bool weather_blows(const WeatherState *weather)
{
    return weather->kind == WEATHER_WIND || weather->kind == WEATHER_STORM;
}

float weather_wind(const WeatherState *weather)
{
    return weather->kind == WEATHER_STORM ? WIND_SPEED * 1.4f : weather->kind == WEATHER_WIND ? WIND_SPEED : 0.0f;
}

float weather_view_top(void)
{
    return -(float)VIEW_TOP / VIEW_SCALE;
}

static void new_drop(WeatherState *w, WeatherBit *d, float camera_x, bool anywhere)
{
    /* Rain covers the sky band too, above the world's viewport. */
    float top = weather_view_top();
    float lead = weather_wind(w) * RAIN_SLANT * ((float)BASELINE - top) / RAIN_SPEED;
    d->x = camera_x - lead - 100.0f + roll(w) * ((float)VIEW_WIDTH + 200.0f + lead);
    d->y = anywhere ? top + roll(w) * ((float)BASELINE - top) : top - roll(w) * 200.0f;
    d->speed = 0.8f + roll(w) * 0.4f;
}

static void new_dust(WeatherState *w, WeatherBit *d, float camera_x, bool anywhere)
{
    float kind = roll(w);
    d->leaf = kind < WEATHER_LEAF_CHANCE;
    d->streak = !d->leaf && kind < WEATHER_LEAF_CHANCE + WEATHER_STREAK_CHANCE;
    d->x = anywhere ? camera_x + roll(w) * (float)VIEW_WIDTH : camera_x - 20.0f - roll(w) * 200.0f;
    /* Dust and leaves low, along the road (not in her way); gusts across the
     * open air above it. */
    d->y = d->streak ? (float)BASELINE - 760.0f + roll(w) * 600.0f
                     : (float)BASELINE - 170.0f + roll(w) * 160.0f;
    d->speed = d->streak ? 1.3f + roll(w) * 0.5f : 0.6f + roll(w) * 0.8f;
}

void weather_start(WeatherState *weather, Weather kind, float camera_x)
{
    memset(weather, 0, sizeof(*weather));
    weather->kind = kind;
    weather->seed = 12345u + (unsigned)kind * 977u;
    for (int i = 0; i < WEATHER_SPLASHES; i++)
        weather->splash_age[i] = 1.0f; /* None yet */
    for (int i = 0; i < WEATHER_DROPS; i++)
        new_drop(weather, &weather->drops[i], camera_x, true);
    for (int i = 0; i < WEATHER_DUST; i++)
        new_dust(weather, &weather->dust[i], camera_x, true);
    weather->tumble_wait = 2.0f;
    weather->flash_wait = 4.0f;
}

static void rain(WeatherState *w, float camera_x, float dt)
{
    float drift = weather_wind(w) * RAIN_SLANT;
    for (int i = 0; i < WEATHER_DROPS; i++) {
        WeatherBit *d = &w->drops[i];
        d->y += RAIN_SPEED * d->speed * dt;
        d->x += drift * d->speed * dt;
        /* Each lands somewhere on the road's depth, below the ground line. */
        float ground = (float)BASELINE + (float)((i * 37) % WEATHER_SPLASH_DEPTH);
        if (d->y < ground)
            continue;
        if (i % 3 == 0) { /* Some leave a splash */
            w->splash_x[w->splash_next] = d->x;
            w->splash_age[w->splash_next] = 0.0f;
            w->splash_next = (w->splash_next + 1) % WEATHER_SPLASHES;
        }
        new_drop(w, d, camera_x, false);
    }
    for (int i = 0; i < WEATHER_SPLASHES; i++)
        w->splash_age[i] += dt;
}

static void blow(WeatherState *w, float camera_x, float dt)
{
    float wind = weather_wind(w);
    for (int i = 0; i < WEATHER_DUST; i++) {
        WeatherBit *d = &w->dust[i];
        d->x += wind * d->speed * dt;
        if (!d->streak)
            d->y += sinf(d->x * 0.01f + (float)i) * (d->leaf ? 40.0f : 12.0f) * dt;
        /* A gust line trails behind its head: it leaves once the tail has. */
        float past = d->streak ? 160.0f : 20.0f;
        if (d->x > camera_x + (float)VIEW_WIDTH + past || d->x < camera_x - 400.0f)
            new_dust(w, d, camera_x, false);
    }
    if (!w->tumbling) {
        w->tumble_wait -= dt;
        if (w->tumble_wait <= 0.0f) {
            w->tumbling = true;
            w->tumble_x = camera_x - 60.0f;
            w->tumble_height = 0.0f;
            w->tumble_vy = 0.0f;
            w->tumble_time = 0.0f;
        }
        return;
    }
    /* Rolling with the wind, hopping on the bumps. */
    w->tumble_time += dt;
    w->tumble_x += wind * 0.55f * dt;
    w->tumble_vy -= 900.0f * dt;
    w->tumble_height += w->tumble_vy * dt;
    if (w->tumble_height <= 0.0f) {
        w->tumble_height = 0.0f;
        w->tumble_vy = 120.0f + roll(w) * 160.0f;
    }
    if (w->tumble_x > camera_x + (float)VIEW_WIDTH + 80.0f) {
        w->tumbling = false;
        w->tumble_wait = TUMBLE_EVERY * (0.6f + roll(w) * 0.8f);
    }
}

void weather_update(WeatherState *weather, float camera_x, float dt)
{
    if (weather_rains(weather))
        rain(weather, camera_x, dt);
    if (weather_blows(weather))
        blow(weather, camera_x, dt);
    if (weather->kind == WEATHER_STORM) { /* Lightning, sometimes twice */
        weather->flash = fmaxf(0.0f, weather->flash - dt * 3.0f);
        weather->flash_wait -= dt;
        if (weather->flash_wait <= 0.0f) {
            weather->flash = 1.0f;
            weather->flash_wait = roll(weather) < 0.35f ? 0.25f : 5.0f + roll(weather) * 8.0f;
        }
    }
}
