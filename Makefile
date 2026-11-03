# Vaquera 2D - C + SDL2 (SDL2_ttf, SDL2_mixer)
#   make          Build build/bin/Vaquera2D
#   make test     Build and run the logic tests (no window)
#   make run      Build and launch the game
#   make watch    Rebuild and relaunch the game on every saved change
#   make clean    Remove build/ (dist/ is managed by build.sh)

CC      ?= cc
PYTHON  ?= python3
BUILD   := build
GEN     := $(BUILD)/generated
BIN     := $(BUILD)/bin/Vaquera2D

SDL_CFLAGS := $(shell pkg-config --cflags sdl2 SDL2_ttf SDL2_mixer)
SDL_LIBS   := $(shell pkg-config --libs sdl2 SDL2_ttf SDL2_mixer)

CFLAGS   ?= -O2 -g
CFLAGS   += -std=c11 -Wall -Wextra -Wpedantic
CPPFLAGS += -Isrc -I$(GEN) -MMD -MP
LDLIBS   += -lm

# Pure game logic: no SDL, shared by the game and the tests.
CORE_SRC := src/engine/input.c src/engine/animation.c src/game/movement.c src/game/jump.c src/game/shoot.c src/game/bullet.c src/game/player.c \
            src/game/damage.c src/game/zombie.c src/game/combat.c src/game/effects.c \
            src/game/camera.c src/game/world.c src/game/props.c src/game/themes.c src/game/smoke.c \
            src/game/progression.c src/game/stages.c src/game/chest.c src/game/stage_run.c \
            src/game/menu.c src/game/weapons.c src/game/characters.c src/game/char_select.c \
            src/game/terrain.c src/game/settings.c src/game/crows.c src/game/weather.c \
            src/game/hallucination.c src/game/almanac.c src/game/lighting.c
APP_SRC  := src/main.c src/engine/platform.c src/engine/assets.c src/engine/text.c src/engine/audio.c src/engine/pixfont.c \
            src/game/controls.c src/game/scene.c src/game/hud.c src/game/player_render.c \
            src/game/bullet_render.c src/game/zombie_render.c src/game/effects_render.c \
            src/game/health_bar.c src/game/smoke_render.c src/game/chest_render.c \
            src/game/character_skin.c src/game/terrain_render.c src/game/ui.c src/game/hang_render.c \
            src/game/weather_render.c src/game/almanac_render.c
GEN_SRC  := $(GEN)/assets_data.c
TESTS    := $(patsubst tests/%.c,$(BUILD)/tests/%,$(wildcard tests/test_*.c))
AUDIO_TEST := $(BUILD)/tests/audio_mixer
ASSETS_LOADER_TEST := $(BUILD)/tests/assets_loader
WEATHER_RENDER_TEST := $(BUILD)/tests/weather_render
STAGE_AUDIO_TEST := $(BUILD)/tests/stage_audio
LIGHTING_RENDER_TEST := $(BUILD)/tests/lighting_render
ZOMBIE_RENDER_TEST := $(BUILD)/tests/zombie_render
SCENE_LIGHTING_TEST := $(BUILD)/tests/scene_lighting
ASSETS   := $(shell find assets -type f \( -name '*.png' -o -name '*.ttf' -o -name '*.wav' -o -name '*.ogg' \))
# The list of asset paths, rewritten only when it changes: moving, renaming or
# deleting a file re-embeds the assets even though no file got newer.
ASSET_LIST := $(GEN)/assets.list
ifneq ($(file <$(ASSET_LIST)),$(sort $(ASSETS)))
$(shell mkdir -p $(GEN))
$(file >$(ASSET_LIST),$(sort $(ASSETS)))
endif

CORE_OBJ := $(CORE_SRC:%.c=$(BUILD)/obj/%.o)
APP_OBJ  := $(APP_SRC:%.c=$(BUILD)/obj/%.o) $(BUILD)/obj/assets_data.o

.PHONY: all test run watch clean
all: $(BIN)

$(GEN)/assets_data.c $(GEN)/assets_data.h &: tools/embed_assets.py $(ASSETS) $(ASSET_LIST)
	@mkdir -p $(GEN)
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tools/embed_assets.py assets $(GEN)

# Every object may include the generated header, so generate it first.
$(BUILD)/obj/%.o: %.c | $(GEN)/assets_data.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(SDL_CFLAGS) $(CFLAGS) -c $< -o $@

$(BUILD)/obj/assets_data.o: $(GEN)/assets_data.c $(GEN)/assets_data.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(BIN): $(CORE_OBJ) $(APP_OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(LDFLAGS) $^ -o $@ $(SDL_LIBS) $(LDLIBS)

$(BUILD)/tests/%: tests/%.c tests/test.h $(CORE_OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(CORE_OBJ) -o $@ $(LDLIBS)

# The mixer integration check has its own tiny embedded WAV fixture and a
# dummy audio device. Keep a console main on Windows as well as on Linux.
$(AUDIO_TEST): tests/audio_mixer.c tests/test.h src/engine/audio.c src/engine/audio.h src/config.h | $(GEN)/assets_data.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/audio_mixer.c src/engine/audio.c -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

# Native RGBA fixtures exceed the former 128-texture limit without linking
# the generated image data or opening a real window.
$(ASSETS_LOADER_TEST): tests/assets_loader.c tests/test.h src/engine/assets.c src/engine/assets.h | $(GEN)/assets_data.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/assets_loader.c src/engine/assets.c -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

$(WEATHER_RENDER_TEST): tests/weather_render.c tests/test.h src/game/weather_render.c src/game/weather_render.h src/game/weather.c src/game/weather.h src/config.h | $(GEN)/assets_data.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/weather_render.c src/game/weather_render.c src/game/weather.c -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

$(STAGE_AUDIO_TEST): tests/stage_audio.c tests/test.h src/main.c $(CORE_OBJ) $(filter-out $(BUILD)/obj/src/main.o $(BUILD)/obj/src/engine/audio.o,$(APP_OBJ))
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/stage_audio.c $(CORE_OBJ) $(filter-out $(BUILD)/obj/src/main.o $(BUILD)/obj/src/engine/audio.o,$(APP_OBJ)) -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

$(LIGHTING_RENDER_TEST): tests/lighting_render.c tests/test.h src/game/terrain_render.c src/game/terrain_render.h src/game/lighting.h $(CORE_OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/lighting_render.c src/game/terrain_render.c $(CORE_OBJ) -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

$(ZOMBIE_RENDER_TEST): tests/zombie_render.c tests/test.h src/game/zombie_render.c src/game/zombie_render.h src/game/health_bar.c src/game/hang_render.c $(CORE_OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/zombie_render.c src/game/zombie_render.c src/game/health_bar.c src/game/hang_render.c $(CORE_OBJ) -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

$(SCENE_LIGHTING_TEST): tests/scene_lighting.c tests/test.h src/game/scene.c src/game/scene.h src/game/terrain_render.c src/game/terrain_render.h $(CORE_OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(filter-out -Dmain=SDL_main,$(SDL_CFLAGS)) $(CFLAGS) tests/scene_lighting.c src/game/scene.c src/game/terrain_render.c $(CORE_OBJ) -o $@ $(filter-out -lmingw32 -mwindows -lSDL2main,$(SDL_LIBS)) $(LDLIBS)

test: $(TESTS) $(AUDIO_TEST) $(ASSETS_LOADER_TEST) $(WEATHER_RENDER_TEST) $(STAGE_AUDIO_TEST) $(LIGHTING_RENDER_TEST) $(ZOMBIE_RENDER_TEST) $(SCENE_LIGHTING_TEST)
	@set -e; for t in $(TESTS) $(AUDIO_TEST) $(ASSETS_LOADER_TEST) $(WEATHER_RENDER_TEST) $(STAGE_AUDIO_TEST) $(LIGHTING_RENDER_TEST) $(ZOMBIE_RENDER_TEST) $(SCENE_LIGHTING_TEST); do $$t; done
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tests/audio_assets.py
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tests/test_zombie_assets.py

run: $(BIN)
	./$(BIN)

watch:
	@./tools/watch.sh

clean:
	rm -rf $(BUILD)

-include $(shell find $(BUILD)/obj -name '*.d' 2>/dev/null)
