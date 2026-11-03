#ifndef GAME_TERRAIN_RENDER_H
#define GAME_TERRAIN_RENDER_H

#include <SDL.h>

#include "game/terrain.h"
#include "game/lighting.h"
#include "game/zombie.h"

/* The road's pieces in view, standing on the ground line (a blown barrel is
 * gone; a wrecked barricade and an empty wagon stay). */
void terrain_render(SDL_Renderer *renderer, const Terrain *terrain, float camera_x);

/* A river's surface again, over the feet of whoever wades it: after them. */
void terrain_render_front(SDL_Renderer *renderer, const Terrain *terrain, float camera_x);

/* Surface illumination, perspective ground shadows and atmospheric bloom.
 * Call after the world/effects, before restoring the window's HUD viewport. */
void terrain_render_lights(SDL_Renderer *renderer, const Lighting *lighting,
                            const Player *player, const Zombie *zombies, int zombie_count,
                            float camera_x);
void terrain_render_surface_lights(SDL_Renderer *renderer, const Lighting *lighting,
                                    const Player *player, const Zombie *zombies, int zombie_count,
                                    float camera_x);
void terrain_render_light_bloom(SDL_Renderer *renderer, const Lighting *lighting, float camera_x);
void terrain_render_shutdown(void);

#endif
