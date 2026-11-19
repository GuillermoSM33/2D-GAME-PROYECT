#include "game/car_pass.h"

#include <math.h>

#include "config.h"

static float art(float px) { return px * (float)SPRITE_SCALE; }

/* A door's handle, world x, on the car whose middle is at car_x. */
static float handle_x(float car_x, int look, int side)
{
    int at = look == CAR_PICKUP_LOOK ? CAR_CAB_HANDLE : side ? CAR_FRONT_HANDLE : CAR_REAR_HANDLE;
    return car_x + art((float)at - (float)CAR_WRECK_W / 2.0f);
}

float car_pass_exit_x(float car_x, int facing)
{
    return car_x + (float)facing * (art((float)CAR_WRECK_W / 2.0f) + PLAYER_BODY_HALF_WIDTH + 12.0f);
}

void car_plan(CarPlan *plan, float from, float car_x, int look, int facing, bool smash)
{
    float f = facing < 0 ? -1.0f : 1.0f;
    plan->facing = facing < 0 ? -1 : 1;
    plan->smash = smash;
    /* Going right she opens the rear door and leaves by the front one. */
    plan->entry_side = plan->facing > 0 ? 0 : 1;
    plan->exit_side = 1 - plan->entry_side;
    float stand = handle_x(car_x, look, plan->entry_side) - f * art(CAR_REACH);
    float in_entry = handle_x(car_x, look, plan->entry_side) + f * art(CAR_INSIDE_AT);
    float in_exit = handle_x(car_x, look, plan->exit_side) + f * art(CAR_INSIDE_AT);
    float out = in_exit + f * art(CAR_OUT_SHIFT);
    float end = car_pass_exit_x(car_x, plan->facing);
    float walk = art(CAR_WALK_SPEED), crawl = art(CAR_CRAWL_SPEED);
    float seconds[CAR_STEPS] = {
        [CAR_STEP_WALK_IN] = fabsf(stand - from) / walk,
        [CAR_STEP_SETTLE] = CAR_SETTLE_MS / 1000.0f,
        [CAR_STEP_REACH] = CAR_REACH_MS / 1000.0f,
        [CAR_STEP_STRIKE] = smash ? CAR_STRIKE_MS / 1000.0f : 0.0f,
        [CAR_STEP_UNLOCK] = smash ? CAR_UNLOCK_MS / 1000.0f : 0.0f,
        [CAR_STEP_PULL] = CAR_PULL_MS / 1000.0f,
        [CAR_STEP_IN] = CAR_STEP_IN_MS / 1000.0f,
        [CAR_STEP_CRAWL] = fmaxf(CAR_CRAWL_MIN_MS / 1000.0f, fabsf(in_exit - in_entry) / crawl),
        [CAR_STEP_PUSH] = CAR_PUSH_MS / 1000.0f,
        [CAR_STEP_OUT] = CAR_STEP_OUT_MS / 1000.0f,
        [CAR_STEP_READY] = CAR_READY_MS / 1000.0f,
        [CAR_STEP_WALK_OUT] = fabsf(end - out) / walk,
    };
    /* Where each step starts. Those that stay put begin where the last ended. */
    float where[CAR_STEPS + 1] = {
        [CAR_STEP_WALK_IN] = from, [CAR_STEP_SETTLE] = stand, [CAR_STEP_REACH] = stand,
        [CAR_STEP_STRIKE] = stand, [CAR_STEP_UNLOCK] = stand, [CAR_STEP_PULL] = stand,
        [CAR_STEP_IN] = stand, [CAR_STEP_CRAWL] = in_entry, [CAR_STEP_PUSH] = in_exit,
        [CAR_STEP_OUT] = in_exit, [CAR_STEP_READY] = out, [CAR_STEP_WALK_OUT] = out,
        [CAR_STEPS] = end,
    };
    plan->at[0] = 0.0f;
    for (int s = 0; s < CAR_STEPS; s++) {
        plan->at[s + 1] = plan->at[s] + seconds[s];
        plan->x[s] = where[s];
    }
    plan->x[CAR_STEPS] = end;
}

CarStep car_plan_step(const CarPlan *plan, float time, float *phase)
{
    for (int s = 0; s < CAR_STEPS; s++) {
        float length = plan->at[s + 1] - plan->at[s];
        if (length <= 0.0f || time >= plan->at[s + 1])
            continue;
        *phase = time <= plan->at[s] ? 0.0f : (time - plan->at[s]) / length;
        return (CarStep)s;
    }
    *phase = 1.0f;
    return CAR_STEP_WALK_OUT;
}

/* The steps that move her: their way is spread evenly over their time (the
 * poses are drawn for that). The others keep her where they began. */
static bool moves(CarStep s)
{
    return s == CAR_STEP_WALK_IN || s == CAR_STEP_IN || s == CAR_STEP_CRAWL || s == CAR_STEP_OUT ||
           s == CAR_STEP_WALK_OUT;
}

float car_plan_x(const CarPlan *plan, float time)
{
    if (time >= plan->at[CAR_STEPS])
        return plan->x[CAR_STEPS];
    float phase;
    CarStep s = car_plan_step(plan, time, &phase);
    if (!moves(s))
        return plan->x[s];
    return plan->x[s] + (plan->x[s + 1] - plan->x[s]) * phase;
}

static int within(int first, int count, float phase)
{
    int frame = (int)(phase * (float)count);
    return first + (frame < 0 ? 0 : frame >= count ? count - 1 : frame);
}

int car_plan_frame(const CarPlan *plan, float time)
{
    float phase;
    CarStep s = car_plan_step(plan, time, &phase);
    switch (s) {
    case CAR_STEP_WALK_IN:
    case CAR_STEP_WALK_OUT: { /* Her feet keep to the ground: the cycle goes by the way walked */
        float walked = fabsf(car_plan_x(plan, time) - plan->x[s]);
        int frame = (int)floorf(walked / art(CAR_STRIDE) * (float)CAR_WALK_FRAMES);
        if (s == CAR_STEP_WALK_OUT)
            frame += CAR_WALK_FRAMES / 2; /* She steps out on the other foot */
        return CAR_WALK_FIRST + frame % CAR_WALK_FRAMES;
    }
    case CAR_STEP_SETTLE: return within(CAR_SETTLE_FIRST, CAR_SETTLE_FRAMES, phase);
    case CAR_STEP_REACH: return within(CAR_REACH_FIRST, CAR_REACH_FRAMES, phase);
    case CAR_STEP_STRIKE: return within(CAR_STRIKE_FIRST, CAR_STRIKE_FRAMES, phase);
    case CAR_STEP_UNLOCK: return within(CAR_UNLOCK_FIRST, CAR_UNLOCK_FRAMES, phase);
    case CAR_STEP_PULL: return within(CAR_PULL_FIRST, CAR_PULL_FRAMES, phase);
    case CAR_STEP_IN: return within(CAR_STEP_IN_FIRST, CAR_STEP_IN_FRAMES, phase);
    case CAR_STEP_CRAWL: {
        float length = plan->at[CAR_STEP_CRAWL + 1] - plan->at[CAR_STEP_CRAWL];
        float cycles = fmaxf(1.0f, roundf(length * 1000.0f / CAR_CRAWL_CYCLE_MS));
        int frame = (int)floorf(phase * cycles * (float)CAR_CRAWL_FRAMES);
        return CAR_CRAWL_FIRST + frame % CAR_CRAWL_FRAMES;
    }
    case CAR_STEP_PUSH: return within(CAR_PUSH_FIRST, CAR_PUSH_FRAMES, phase);
    case CAR_STEP_OUT: return within(CAR_STEP_OUT_FIRST, CAR_STEP_OUT_FRAMES, phase);
    case CAR_STEP_READY: return within(CAR_READY_FIRST, CAR_READY_FRAMES, phase);
    default: return CAR_WALK_FIRST;
    }
}

int car_plan_doors(const CarPlan *plan, float time, int broken)
{
    float phase;
    CarStep s = car_plan_step(plan, time, &phase);
    int ajar_in = 1 + 2 * plan->entry_side, open_in = ajar_in + 1;
    int ajar_out = 1 + 2 * plan->exit_side, open_out = ajar_out + 1;
    int doors = 0;
    if (time >= plan->at[CAR_STEPS])
        doors = 0;
    else if (s == CAR_STEP_PULL)
        doors = phase < 0.5f ? ajar_in : open_in;
    else if (s == CAR_STEP_IN) /* Lying down, she pulls it to */
        doors = phase < 0.625f ? open_in : phase < 0.8f ? ajar_in : 0;
    else if (s == CAR_STEP_PUSH) /* Sitting up, she pushes the other open */
        doors = phase < 0.5f ? ajar_out : open_out;
    else if (s == CAR_STEP_OUT)
        doors = open_out;
    else if (s == CAR_STEP_READY) /* ...and shoves it shut behind her */
        doors = phase < 0.4f ? open_out : phase < 0.75f ? ajar_out : 0;
    if (broken < 0 || broken > 2)
        broken = 0;
    return broken * CAR_DOOR_KINDS + doors;
}

bool car_plan_glass_down(const CarPlan *plan, float time)
{
    if (!plan->smash)
        return true;
    float strike = plan->at[CAR_STEP_STRIKE], length = plan->at[CAR_STEP_STRIKE + 1] - strike;
    return time >= strike + length * (float)CAR_STRIKE_LAND / (float)CAR_STRIKE_FRAMES;
}

float car_plan_action(const CarPlan *plan)
{
    if (plan->smash)
        return plan->at[CAR_STEP_STRIKE] + (plan->at[CAR_STEP_STRIKE + 1] - plan->at[CAR_STEP_STRIKE]) *
                                               (float)CAR_STRIKE_HIT / (float)CAR_STRIKE_FRAMES;
    return plan->at[CAR_STEP_PULL];
}
