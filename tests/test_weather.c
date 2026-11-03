#include <math.h>

#include "config.h"
#include "game/stages.h"
#include "game/weather.h"
#include "test.h"

static void test_rain_falls_and_splashes(void)
{
    WeatherState w;
    weather_start(&w, WEATHER_RAIN, 1000.0f);
    float y = w.drops[0].y;
    weather_update(&w, 1000.0f, FIXED_DT);
    CHECK(w.drops[0].y > y || w.drops[0].y < 0.0f);
    bool splashed = false;
    for (int i = 0; i < 120; i++) {
        weather_update(&w, 1000.0f, FIXED_DT);
        for (int k = 0; k < WEATHER_SPLASHES; k++)
            splashed |= w.splash_age[k] < 0.1f;
    }
    CHECK(splashed && !w.tumbling && w.flash == 0.0f); /* No wind, no storm */
}

static void test_wind_rolls_a_tumbleweed(void)
{
    WeatherState w;
    weather_start(&w, WEATHER_WIND, 1000.0f);
    float x = w.dust[0].x;
    weather_update(&w, 1000.0f, FIXED_DT);
    CHECK(w.dust[0].x > x || w.dust[0].x < 1000.0f);
    bool rolled = false;
    for (int i = 0; i < 400; i++) {
        weather_update(&w, 1000.0f, FIXED_DT);
        rolled |= w.tumbling;
    }
    CHECK(rolled && weather_wind(&w) > 0.0f && !weather_rains(&w));
}

static void test_storm_has_lightning(void)
{
    WeatherState w;
    weather_start(&w, WEATHER_STORM, 0.0f);
    bool flashed = false;
    for (int i = 0; i < 1200; i++) {
        weather_update(&w, 0.0f, FIXED_DT);
        flashed |= w.flash > 0.5f;
    }
    CHECK(flashed && weather_rains(&w) && weather_blows(&w));
}

static void test_every_stage_has_its_weather(void)
{
    CHECK(STAGES[0].weather == WEATHER_WIND && STAGES[STAGE_COUNT - 1].weather == WEATHER_STORM);
}

int main(void)
{
    RUN(test_rain_falls_and_splashes);
    RUN(test_wind_rolls_a_tumbleweed);
    RUN(test_storm_has_lightning);
    RUN(test_every_stage_has_its_weather);
    return TEST_EXIT();
}
