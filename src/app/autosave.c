#include "app/autosave.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

StorageLoad autosave_init(Autosave *save, bool enabled, const char *directory)
{
    memset(save, 0, sizeof(*save));
    save_game_init(&save->game);
    save->enabled = enabled;
    if (!enabled)
        return STORAGE_EMPTY;
    save->store = storage_open(directory);
    if (!save->store) {
        save->failed = true;
        save->feedback_time = 8.0f;
        fprintf(stderr, "No se pudo iniciar el autoguardado.\n");
        return STORAGE_INVALID;
    }
    StorageLoad loaded = storage_load(save->store, save_game_decode, &save->game);
    if (loaded == STORAGE_INVALID) {
        fprintf(stderr, "No se encontró una copia válida del avance; se inicia un perfil nuevo.\n");
        save->failed = true;
        save->feedback_time = 8.0f;
    } else if (loaded == STORAGE_RECOVERED) {
        fprintf(stderr, "Avance recuperado de la copia anterior.\n");
    }
    return loaded;
}

bool autosave_tick(Autosave *save, double seconds, bool playing)
{
    if (!save->enabled || !isfinite(seconds) || seconds < 0.0)
        return false;
    float dt = (float)fmin(seconds, 10.0);
    save->feedback_time = fmaxf(0.0f, save->feedback_time - dt);
    save->feedback_age += dt;
    save->retry_wait = fmaxf(0.0f, save->retry_wait - dt);
    if (playing)
        save->elapsed += seconds;
    uint64_t completed;
    bool success;
    if (storage_result(save->store, &completed, &success) && completed != save->observed) {
        save->observed = completed;
        if (completed >= save->submitted) {
            save->failed = !success;
            save->feedback_time = success ? 2.5f : 8.0f;
            save->feedback_age = 0.0f;
            if (!success) {
                save->elapsed = AUTOSAVE_SECONDS;
                save->retry_wait = 30.0f;
                fprintf(stderr, "No se pudo guardar el avance; se reintentará sin detener la partida.\n");
            }
        }
    }
    save->saving = storage_busy(save->store);
    return playing && save->store && save->elapsed >= AUTOSAVE_SECONDS &&
           save->retry_wait <= 0.0f && !save->saving;
}

bool autosave_request(Autosave *save, const Profile *profiles, int hero,
                       const Volumes *volumes, const StagePlay *active)
{
    if (!save->enabled)
        return true;
    size_t size;
    save_game_snapshot(&save->game, profiles, hero, volumes, active);
    uint64_t job = save->store && save_game_encode(&save->game, save->bytes, sizeof(save->bytes), &size)
        ? storage_submit(save->store, save->bytes, size) : 0;
    save->failed = job == 0;
    save->saving = job != 0;
    save->feedback_time = job ? 2.5f : 8.0f;
    save->feedback_age = 0.0f;
    if (job) {
        save->submitted = job;
        save->elapsed = 0.0;
    } else {
        save->retry_wait = 30.0f;
    }
    return job != 0;
}

void autosave_shutdown(Autosave *save)
{
    if (save->store && !storage_close(save->store)) {
        save->failed = true;
        fprintf(stderr, "No se pudo completar el último guardado. La copia anterior sigue disponible.\n");
    }
    save->store = NULL;
    save->saving = false;
}
