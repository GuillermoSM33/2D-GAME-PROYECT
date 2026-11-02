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
            src/game/terrain.c src/game/settings.c
APP_SRC  := src/main.c src/engine/platform.c src/engine/assets.c src/engine/text.c src/engine/audio.c src/engine/pixfont.c \
            src/game/controls.c src/game/scene.c src/game/hud.c src/game/player_render.c \
            src/game/bullet_render.c src/game/zombie_render.c src/game/effects_render.c \
            src/game/health_bar.c src/game/smoke_render.c src/game/chest_render.c \
            src/game/character_skin.c src/game/terrain_render.c src/game/ui.c
GEN_SRC  := $(GEN)/assets_data.c
TESTS    := $(patsubst tests/%.c,$(BUILD)/tests/%,$(wildcard tests/test_*.c))
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

test: $(TESTS)
	@set -e; for t in $(TESTS); do $$t; done

run: $(BIN)
	./$(BIN)

watch:
	@./tools/watch.sh

clean:
	rm -rf $(BUILD)

-include $(shell find $(BUILD)/obj -name '*.d' 2>/dev/null)
