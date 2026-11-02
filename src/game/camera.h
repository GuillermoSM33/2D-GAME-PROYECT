#ifndef GAME_CAMERA_H
#define GAME_CAMERA_H

/* World x shown at the window's left edge: the player stands a third of the
 * way in (CAMERA_PLAYER_SHARE), so most of the view is the road ahead, and it
 * stops at the ends of the world. It depends only on the player's position,
 * so logic (wakes, bullets) and drawing always agree on it. */
float camera_left(float player_x);

#endif
