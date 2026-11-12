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

static void test_rain_already_covers_upper_sky(void)
{
    CHECK_NEAR((float)VIEW_TOP + weather_view_top() * VIEW_SCALE, 0.0f, 0.001f);
    for (int kind = WEATHER_RAIN; kind <= WEATHER_STORM; kind++) {
        WeatherState w;
        weather_start(&w, (Weather)kind, 2400.0f);
        bool near_window_top = false, over_road = false;
        bool zones[4] = {false};
        for (int i = 0; i < WEATHER_DROPS; i++) {
            float y = w.drops[i].y;
            CHECK(y >= weather_view_top() && y <= (float)BASELINE);
            float screen_y = (float)VIEW_TOP + y * VIEW_SCALE;
            bool visible_x = w.drops[i].x >= 2400.0f && w.drops[i].x < 2400.0f + (float)VIEW_WIDTH;
            near_window_top |= visible_x && screen_y >= 0.0f && screen_y < 30.0f;
            over_road |= visible_x && y > (float)BASELINE - 80.0f;
            /* Full-window views start at y=0; a separate sky band used to
             * require negative view coordinates. Check coverage in each
             * quarter of the visible rain height for either layout. */
            float rain_height = (float)VIEW_TOP + (float)BASELINE * VIEW_SCALE;
            int zone = (int)(screen_y * 4.0f / rain_height);
            if (visible_x && zone >= 0 && zone < 4)
                zones[zone] = true;
        }
        CHECK(near_window_top && over_road);
        for (int zone = 0; zone < 4; zone++)
            CHECK(zones[zone]);
    }
}

static void test_respawned_rain_enters_above_the_entire_window(void)
{
    for (int kind = WEATHER_RAIN; kind <= WEATHER_STORM; kind++) {
        WeatherState w;
        weather_start(&w, (Weather)kind, 5000.0f);
        for (int i = 0; i < WEATHER_DROPS; i++)
            w.drops[i].y = (float)BASELINE + (float)WEATHER_SPLASH_DEPTH;
        weather_update(&w, 5000.0f, FIXED_DT);
        for (int i = 0; i < WEATHER_DROPS; i++) {
            CHECK(w.drops[i].y <= weather_view_top());
            CHECK(w.drops[i].y >= weather_view_top() - 200.0f);
        }
        bool crossed_upper_sky = false;
        for (int frame = 0; frame < 30; frame++) {
            weather_update(&w, 5000.0f, FIXED_DT);
            for (int i = 0; i < WEATHER_DROPS; i++) {
                float screen_y = (float)VIEW_TOP + w.drops[i].y * VIEW_SCALE;
                bool visible_x = w.drops[i].x >= 5000.0f && w.drops[i].x < 5000.0f + (float)VIEW_WIDTH;
                crossed_upper_sky |= visible_x && screen_y >= 0.0f && screen_y < (float)HUD_BAND;
            }
        }
        CHECK(crossed_upper_sky);
    }
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
    CHECK_NEAR(weather_wind(&w), WIND_SPEED, 0.001f);
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
    CHECK_NEAR(weather_wind(&w), WIND_SPEED * 1.4f, 0.001f);
}

static void test_every_stage_has_its_weather(void)
{
    CHECK(STAGES[0].weather == WEATHER_WIND && STAGES[4].weather == WEATHER_STORM && STAGES[8].weather == WEATHER_STORM);
}

int main(void)
{
    RUN(test_rain_falls_and_splashes);
    RUN(test_rain_already_covers_upper_sky);
    RUN(test_respawned_rain_enters_above_the_entire_window);
    RUN(test_wind_rolls_a_tumbleweed);
    RUN(test_storm_has_lightning);
    RUN(test_every_stage_has_its_weather);
    return TEST_EXIT();
}
