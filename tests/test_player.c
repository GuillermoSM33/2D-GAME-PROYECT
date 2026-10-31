#include <string.h>

#include "config.h"
#include "game/movement.h"
#include "game/player.h"
#include "test.h"

static void step(Player *player, InputState *input, bool left, bool right, bool run, int frames)
{
    bool down[ACTION_COUNT];
    for (int i = 0; i < frames; i++) {
        memset(down, 0, sizeof(down));
        down[ACTION_LEFT] = left;
        down[ACTION_RIGHT] = right;
        down[ACTION_RUN] = run;
        input_update(input, down);
        player_update(player, input, FIXED_DT);
    }
}

static void press_jump(Player *player, InputState *input, bool right)
{
    bool down[ACTION_COUNT] = {0};
    down[ACTION_RIGHT] = right;
    down[ACTION_JUMP] = true;
    input_update(input, down);
    player_update(player, input, FIXED_DT);
}

static void click(Player *player, InputState *input, bool left, bool right)
{
    bool down[ACTION_COUNT] = {0};
    down[ACTION_LEFT] = left;
    down[ACTION_RIGHT] = right;
    down[ACTION_SHOOT] = true;
    input_update(input, down);
    player_update(player, input, FIXED_DT);
}

static int shot_steps(void)
{
    return (int)(PLAYER_SHOOT_FRAMES / PLAYER_SHOOT_FPS / FIXED_DT) + 2;
}

static int air_steps(void)
{
    return (int)(PLAYER_JUMP_TIME / FIXED_DT) + 1;
}

static void test_starts_idle(void)
{
    Player player;
    player_init(&player);
    CHECK(player.state == PLAYER_IDLE);
    CHECK(player.facing == FACING_RIGHT);
    CHECK(player.anim.frame == 0);
    CHECK_NEAR(player.x, PLAYER_START_X, 0.01f);
}

static void test_walk_speed(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 60);
    CHECK(player.state == PLAYER_WALK);
    CHECK_NEAR(player.x, PLAYER_START_X + PLAYER_WALK_SPEED, 0.5f);
}

static void test_run_is_faster(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, true, 60);
    CHECK(player.state == PLAYER_RUN);
    CHECK_NEAR(player.x, PLAYER_START_X + PLAYER_WALK_SPEED * PLAYER_RUN_SPEED_MULT, 0.5f);
}

static void test_turns_and_stops(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 20);
    step(&player, &input, true, false, false, 5);
    CHECK(player.facing == FACING_LEFT);
    step(&player, &input, false, false, false, 1);
    CHECK(player.state == PLAYER_IDLE);
    CHECK(player.facing == FACING_LEFT); /* Keeps looking the last way */
    CHECK(player.anim.frame == 0);
}

static void test_both_keys_last_wins(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 5);
    float x = player.x;
    step(&player, &input, true, true, false, 10);
    CHECK(player.facing == FACING_LEFT);
    CHECK(player.x < x);
    CHECK(player.state == PLAYER_WALK);
}

static void test_stays_inside_window(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, true, false, true, 600);
    CHECK_NEAR(player.x, movement_min_x(), 0.01f);
    step(&player, &input, false, true, true, 600);
    CHECK_NEAR(player.x, movement_max_x(), 0.01f);
}

static void test_reset(void)
{
    Player player;
    InputState input;
    bool down[ACTION_COUNT] = {0};
    player_init(&player);
    input_init(&input);
    step(&player, &input, true, false, false, 30);
    down[ACTION_RESET] = true;
    input_update(&input, down);
    player_update(&player, &input, FIXED_DT);
    CHECK_NEAR(player.x, PLAYER_START_X, 0.01f);
    CHECK(player.facing == FACING_RIGHT);
}

static void test_walking_jump_right(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 10);
    float x = player.x;
    press_jump(&player, &input, true);
    CHECK(player.state == PLAYER_JUMP);
    CHECK(player.jump.airborne);

    float peak = 0.0f;
    unsigned frames = 0;
    for (int i = 0; i < air_steps() && player.jump.airborne; i++) {
        step(&player, &input, false, true, false, 1);
        frames |= 1u << player.anim.frame;
        if (player.jump.height > peak)
            peak = player.jump.height;
    }
    CHECK(!player.jump.airborne);
    CHECK(player.state == PLAYER_LAND);
    CHECK_NEAR(peak, PLAYER_JUMP_HEIGHT, 1.0f);
    CHECK((frames & 0x3Fu) == 0x3Fu); /* All six air frames shown */
    CHECK(player.x > x + PLAYER_WALK_SPEED * PLAYER_JUMP_TIME * 0.9f); /* Kept moving */
    CHECK(player.facing == FACING_RIGHT);

    step(&player, &input, false, true, false, 12); /* Landing finishes */
    CHECK(player.state == PLAYER_WALK);
}

static void test_no_double_jump(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    press_jump(&player, &input, false);
    step(&player, &input, false, false, false, 10);
    float t = player.jump.time;
    press_jump(&player, &input, false); /* Mid-air: ignored */
    CHECK(player.jump.time > t);
    CHECK(player.state == PLAYER_JUMP);
}

static void test_holding_jump_does_not_repeat(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    for (int i = 0; i < air_steps() + 30; i++)
        press_jump(&player, &input, false); /* Key held the whole time */
    CHECK(!player.jump.airborne);
    CHECK(player.state == PLAYER_IDLE);
}

static void test_jump_from_landing(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    press_jump(&player, &input, false);
    step(&player, &input, false, false, false, air_steps());
    CHECK(player.state == PLAYER_LAND);
    press_jump(&player, &input, false);
    CHECK(player.state == PLAYER_JUMP);
}

static void test_shoot_standing(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    click(&player, &input, false, false);
    CHECK(player.state == PLAYER_SHOOT);
    int fires = player.shot_fired;
    for (int i = 0; i < shot_steps(); i++) {
        step(&player, &input, false, false, false, 1);
        fires += player.shot_fired;
    }
    CHECK(fires == 1);
    CHECK(player.state == PLAYER_IDLE);
    CHECK(player.anim.frame == 0);
}

static void test_shooting_plants_feet(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 10);
    click(&player, &input, false, true);
    float x = player.x;
    step(&player, &input, false, true, true, 10); /* Still holding right + shift */
    CHECK(player.state == PLAYER_SHOOT);
    CHECK_NEAR(player.x, x, 0.001f);
    step(&player, &input, false, true, false, shot_steps());
    CHECK(player.state == PLAYER_WALK); /* Walks again once the shot ends */
    CHECK(player.x > x);
}

static void test_shoot_faces_held_direction(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    CHECK(player.facing == FACING_RIGHT);
    click(&player, &input, true, false);
    CHECK(player.state == PLAYER_SHOOT);
    CHECK(player.facing == FACING_LEFT);
}

static void test_no_shooting_in_the_air(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    press_jump(&player, &input, false);
    step(&player, &input, false, false, false, 5);
    click(&player, &input, false, false);
    CHECK(player.state == PLAYER_JUMP);
    CHECK(!player.shot.active);
}

static void test_jump_cancels_shot(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    click(&player, &input, false, false);
    step(&player, &input, false, false, false, 3);
    press_jump(&player, &input, false);
    CHECK(player.state == PLAYER_JUMP);
    CHECK(!player.shot.active);
}

static void test_reset_cancels_shot(void)
{
    Player player;
    InputState input;
    bool down[ACTION_COUNT] = {0};
    player_init(&player);
    input_init(&input);
    click(&player, &input, false, false);
    down[ACTION_RESET] = true;
    input_update(&input, down);
    player_update(&player, &input, FIXED_DT);
    CHECK(player.state == PLAYER_IDLE);
    CHECK(!player.shot.active);
}

static void test_muzzle_follows_facing(void)
{
    Player player;
    float x, y;
    player_init(&player);
    player_muzzle(&player, &x, &y);
    CHECK_NEAR(x, player.x + PLAYER_MUZZLE_DX * SPRITE_SCALE, 0.01f);
    CHECK_NEAR(y, BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE, 0.01f);
    player.facing = FACING_LEFT;
    player_muzzle(&player, &x, &y);
    CHECK_NEAR(x, player.x - PLAYER_MUZZLE_DX * SPRITE_SCALE, 0.01f);
}

static void test_short_tap_moves_a_leg(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    step(&player, &input, false, true, false, 1);
    CHECK(player.state == PLAYER_WALK);
    CHECK(player.anim.frame == 1); /* First step at once, not the standing pose */
    step(&player, &input, false, true, false, 6);
    CHECK(player.anim.frame == 2); /* Then the cycle keeps its usual pace */
    step(&player, &input, false, false, false, 1);
    step(&player, &input, true, false, false, 1);
    CHECK(player.anim.frame == 1); /* A new tap starts stepping again */
}

static void test_hit_pushes_and_blinks(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    CHECK(player.health == PLAYER_HEALTH);
    CHECK(!player_hit(&player, 15.0f, -1));
    CHECK(player.health == PLAYER_HEALTH - 12); /* 25 armor stops a fifth */
    CHECK(player.hurt_time > 0.0f);
    step(&player, &input, false, false, false, 30);
    CHECK_NEAR(player.x, PLAYER_START_X - PLAYER_KNOCKBACK_SPEED * PLAYER_KNOCKBACK_TIME, 0.5f);
    CHECK(player.hurt_time == 0.0f);
    CHECK(player.state == PLAYER_IDLE);
}

static void test_dead_ignores_input_until_reset(void)
{
    Player player;
    InputState input;
    bool down[ACTION_COUNT] = {0};
    player_init(&player);
    input_init(&input);
    player.health = 5;
    CHECK(player_hit(&player, 15.0f, 1));
    CHECK(!player_alive(&player));
    CHECK(player.health == 0);
    step(&player, &input, false, false, false, 30); /* Let the push finish */
    float x = player.x;
    step(&player, &input, false, true, true, 30);
    click(&player, &input, false, false);
    press_jump(&player, &input, false);
    CHECK(player.x == x);
    CHECK(!player.jump.airborne);
    CHECK(player.state == PLAYER_DEAD);
    CHECK(!player_hit(&player, 15.0f, 1)); /* Already down */
    input_init(&input);
    down[ACTION_RESET] = true;
    input_update(&input, down);
    player_update(&player, &input, FIXED_DT);
    CHECK(player_alive(&player));
    CHECK(player.health == PLAYER_HEALTH);
}

static void test_death_mid_shot_holsters(void)
{
    Player player;
    InputState input;
    player_init(&player);
    input_init(&input);
    click(&player, &input, false, false);
    CHECK(player.state == PLAYER_SHOOT);
    player.health = 1;
    player_hit(&player, 15.0f, 1);
    step(&player, &input, false, false, false, shot_steps());
    CHECK(!player.shot.active);
    CHECK(player.anim.frame == 0); /* Standing frame, no shot frames */
}

int main(void)
{
    printf("test_player\n");
    RUN(test_starts_idle);
    RUN(test_walk_speed);
    RUN(test_run_is_faster);
    RUN(test_turns_and_stops);
    RUN(test_both_keys_last_wins);
    RUN(test_stays_inside_window);
    RUN(test_reset);
    RUN(test_walking_jump_right);
    RUN(test_no_double_jump);
    RUN(test_holding_jump_does_not_repeat);
    RUN(test_jump_from_landing);
    RUN(test_shoot_standing);
    RUN(test_shooting_plants_feet);
    RUN(test_shoot_faces_held_direction);
    RUN(test_no_shooting_in_the_air);
    RUN(test_jump_cancels_shot);
    RUN(test_reset_cancels_shot);
    RUN(test_muzzle_follows_facing);
    RUN(test_short_tap_moves_a_leg);
    RUN(test_hit_pushes_and_blinks);
    RUN(test_dead_ignores_input_until_reset);
    RUN(test_death_mid_shot_holsters);
    return TEST_EXIT();
}
