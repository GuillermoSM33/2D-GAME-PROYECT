#ifndef GAME_CATCH_H
#define GAME_CATCH_H

/* What holds a body caught in a trap that hangs it up (stage_run.c). */
typedef enum {
    CATCH_NONE,  /* Not hanging (a bear trap holds it on the ground) */
    CATCH_NET,   /* Up in a net bag */
    CATCH_SNARE  /* Head down by one foot from a sapling */
} CatchKind;

#endif
