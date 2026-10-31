#ifndef ENGINE_ANIMATION_H
#define ENGINE_ANIMATION_H

#include <stdbool.h>

/* A strip of equally sized frames laid out in one row of a sprite sheet,
 * drawn facing right. Nothing in the PNG marks where a frame ends: frame i
 * is simply the rectangle (i * frame_w, 0, frame_w, frame_h). */
typedef struct {
    const char *sheet; /* Embedded asset name, e.g. "sprites/player/walk" */
    int frame_w;
    int frame_h;
    int first_frame;
    int frame_count;
    float fps;
    bool loop;
    /* Pivot inside the frame, in art pixels: the body's horizontal center and
     * the row where the feet touch the ground. Lets sheets of different sizes
     * line up, and keeps the body in place when the frame is mirrored. */
    float anchor_x;
    int ground_y;
} AnimationDef;

typedef struct {
    const AnimationDef *def;
    float time;
    int frame;     /* Index within the sheet (first_frame + offset) */
    bool finished; /* Only for non-looping animations */
} Animation;

/* Switch to def. Restarts only when def differs from the current one. */
void animation_play(Animation *anim, const AnimationDef *def);
void animation_restart(Animation *anim);
void animation_update(Animation *anim, float dt);

/* Continue playing from a given frame (offset from first_frame), as if it had
 * just been reached. */
void animation_seek(Animation *anim, int offset);

/* Show a given frame (offset from first_frame, clamped) chosen by game logic. */
void animation_set_frame(Animation *anim, int offset);

/* Pick the frame from external progress (0..1) instead of time, e.g. to
 * follow a jump arc. */
void animation_set_progress(Animation *anim, float progress);

#endif
