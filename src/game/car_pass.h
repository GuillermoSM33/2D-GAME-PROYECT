#ifndef GAME_CAR_PASS_H
#define GAME_CAR_PASS_H
/* Through a car across the road (N). She walks to a door and opens it (or
 * breaks its glass and lifts the lock), steps in on the sill and sits on the
 * floor under the roof, shoves herself across out of sight, puts a leg
 * out of the other door, stands up and walks on as it shuts.
 *
 * tools/make_car_passage.py reads every CAR_* number here: its poses are
 * drawn for these frames and distances. Change them on both sides. */
#include <stdbool.h>

/* Her sheet (characters/<id>/car): CAR_FRAME_W x CAR_FRAME_H cells in two
 * rows. Row 0 is what of her is out of the car, drawn over it; row 1 what is
 * in it, drawn under its body and doors. */
#define CAR_FRAME_W 81
#define CAR_FRAME_H 80
#define CAR_WALK_FIRST 0      /* A walk cycle, by distance: to the door and away */
#define CAR_WALK_FRAMES 8
#define CAR_SETTLE_FIRST 8    /* Hands free (the SWAT slings his gun) */
#define CAR_SETTLE_FRAMES 2
#define CAR_REACH_FIRST 10    /* Her hand to the handle */
#define CAR_REACH_FRAMES 3
#define CAR_STRIKE_FIRST 13   /* Locked: her fist through the glass (CAR_STRIKE_HIT breaks it)... */
#define CAR_STRIKE_FRAMES 6
#define CAR_STRIKE_HIT 2
#define CAR_STRIKE_LAND 5     /* ...its bits down on the road (terrain/car_glass) */
#define CAR_UNLOCK_FIRST 19   /* ...and her arm in through it to the lock */
#define CAR_UNLOCK_FRAMES 3
#define CAR_PULL_FIRST 22     /* The door swung open */
#define CAR_PULL_FRAMES 4
#define CAR_STEP_IN_FIRST 26  /* A foot on the sill, ducking in, sitting down */
#define CAR_STEP_IN_FRAMES 8
#define CAR_CRAWL_FIRST 34    /* Sliding across the seats, a cycle */
#define CAR_CRAWL_FRAMES 6
#define CAR_PUSH_FIRST 40     /* The other door pushed open */
#define CAR_PUSH_FRAMES 3
#define CAR_STEP_OUT_FIRST 43 /* A leg out, her head out, up on her feet */
#define CAR_STEP_OUT_FRAMES 8
#define CAR_READY_FIRST 51    /* The door shut behind her (the SWAT's gun back in his hands) */
#define CAR_READY_FRAMES 4
#define CAR_PASS_FRAMES 55

/* The steps that take the same time on every car, in milliseconds. */
#define CAR_SETTLE_MS 120
#define CAR_REACH_MS 180
#define CAR_STRIKE_MS 480
#define CAR_UNLOCK_MS 260
#define CAR_PULL_MS 260
#define CAR_STEP_IN_MS 560
#define CAR_CRAWL_MIN_MS 240
#define CAR_PUSH_MS 180
#define CAR_STEP_OUT_MS 560
#define CAR_READY_MS 280

/* Distances, art px. Walking and sliding across take as long as their way. */
#define CAR_STRIDE 30         /* One walk cycle */
#define CAR_WALK_SPEED 100    /* A second */
#define CAR_CRAWL_SPEED 70
#define CAR_CRAWL_CYCLE_MS 360
#define CAR_REACH 22          /* From where she stands to the handle she opens, at arm's length */
/* In the car she sits on the floor under the roof, out of sight, this
 * far from the handle of the door she came in by and then of the one she
 * leaves by (the same for the pickup's one door: she never goes back). */
#define CAR_INSIDE_AT (-5)
#define CAR_OUT_SHIFT 8      /* From there to where she stands out of the door */
/* Each door's handle, art px from the left of the car's frame (136 wide, not
 * turned round with her): the rear door, the front one, and the pickup's
 * only door, at its cab (she goes in and out by it). */
#define CAR_REAR_HANDLE 60
#define CAR_FRONT_HANDLE 85
#define CAR_CAB_HANDLE 92
#define CAR_PICKUP_LOOK 1

/* The car's layers (terrain/car_passage...): per look, the glass (whole, the
 * rear door's broken, the front's) times its doors (shut, rear ajar, rear
 * open, front ajar, front open). */
#define CAR_DOOR_KINDS 5
#define CAR_DOOR_STATES (3 * CAR_DOOR_KINDS)
#define CAR_PASS_MAX_SECONDS 12.0f /* No crossing takes longer (a saved one is checked) */

typedef enum {
    CAR_STEP_WALK_IN,
    CAR_STEP_SETTLE,
    CAR_STEP_REACH,
    CAR_STEP_STRIKE, /* Only when it is locked */
    CAR_STEP_UNLOCK, /* ...likewise */
    CAR_STEP_PULL,
    CAR_STEP_IN,
    CAR_STEP_CRAWL,
    CAR_STEP_PUSH,
    CAR_STEP_OUT,
    CAR_STEP_READY,
    CAR_STEP_WALK_OUT,
    CAR_STEPS
} CarStep;

/* One crossing, worked out from where it starts: when each step begins
 * (seconds; at[CAR_STEPS] is the end) and where she is then (world x). */
typedef struct {
    float at[CAR_STEPS + 1];
    float x[CAR_STEPS + 1];
    int facing;     /* +1 right, -1 left */
    int entry_side; /* 0 the rear door, 1 the front one */
    int exit_side;
    bool smash;
} CarPlan;

/* From x (world), the car's middle at car_x, its look, the way she faces and
 * whether its glass must break. */
void car_plan(CarPlan *plan, float from, float car_x, int look, int facing, bool smash);
/* Where a crossing of the car at car_x leaves her (world x). */
float car_pass_exit_x(float car_x, int facing);
CarStep car_plan_step(const CarPlan *plan, float time, float *phase);
float car_plan_x(const CarPlan *plan, float time);
int car_plan_frame(const CarPlan *plan, float time);
/* The car's state for its layers: glass (0 whole, 1 rear broken, 2 front
 * broken) times CAR_DOOR_KINDS plus its doors at that time. */
int car_plan_doors(const CarPlan *plan, float time, int broken);
/* When the handle gives (or the glass breaks): the car's flags change then. */
float car_plan_action(const CarPlan *plan);
/* Whether the glass she broke has fallen to the road by then (as soon as it
 * breaks, the bits are still falling in her own frames). */
bool car_plan_glass_down(const CarPlan *plan, float time);

#endif
