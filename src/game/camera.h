#ifndef GAME_CAMERA_H
#define GAME_CAMERA_H

/* World x shown at the window's left edge: the view is centered on the
 * player and stops at the ends of the world. It depends only on the player's
 * position, so logic (spawns, bullets) and drawing always agree on it. */
float camera_left(float player_x);

#endif
