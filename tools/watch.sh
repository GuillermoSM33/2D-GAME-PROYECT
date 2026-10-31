#!/usr/bin/env bash
# Recompila y reabre el juego cada vez que guardas un cambio.
#   make watch   (o ./tools/watch.sh)
# Vigila src/, tests/, assets/, tools/ y el Makefile. Si la compilación o las
# pruebas fallan, muestra el error y deja abierta la versión anterior.
# Ctrl+C para salir (cierra también el juego).
set -uo pipefail
cd "$(dirname "$0")/.."

BIN=build/bin/Vaquera2D
WATCHED=(src tests assets tools Makefile)
INTERVAL=0.5
LOG=build/watch-tests.log
JOBS="$(nproc 2>/dev/null || echo 2)"
game_pid=""

say() { printf '\033[1;36m[watch %s]\033[0m %s\n' "$(date +%H:%M:%S)" "$1"; }

# Firma de los archivos vigilados: cambia al guardar, crear o borrar uno.
signature() {
    find "${WATCHED[@]}" -type f ! -name '*.pyc' -printf '%p %T@ %s\n' 2>/dev/null | sort | md5sum
}

stop_game() {
    if [[ -n "$game_pid" ]] && kill -0 "$game_pid" 2>/dev/null; then
        kill "$game_pid" 2>/dev/null
        wait "$game_pid" 2>/dev/null
    fi
    game_pid=""
}

start_game() {
    stop_game
    "./$BIN" &
    game_pid=$!
    say "Juego abierto (pid $game_pid)."
}

rebuild() {
    say "Compilando..."
    mkdir -p build
    if make -s -j"$JOBS" >/dev/null && make -s -j"$JOBS" test >"$LOG" 2>&1; then
        say "OK."
        start_game
    else
        # Muestra la salida de las pruebas solo si fueron ellas las que fallaron.
        [[ -s "$LOG" ]] && grep -v '^  ok ' "$LOG"
        printf '\033[1;31m[watch] Falló la compilación o las pruebas. Corrige y guarda de nuevo.\033[0m\n'
        [[ -n "$game_pid" ]] && say "Sigue abierta la versión anterior."
    fi
    rm -f "$LOG"
}

# El juego corre en segundo plano y por eso ignora Ctrl+C: hay que cerrarlo
# aquí, salga el vigilante por la razón que sea.
cleanup() {
    trap - EXIT INT TERM HUP
    printf '\n'
    say "Saliendo."
    stop_game
    rm -f "$LOG"
    exit 0
}
trap cleanup EXIT INT TERM HUP

say "Vigilando ${WATCHED[*]} (Ctrl+C para salir)."
last="$(signature)"
rebuild
while true; do
    sleep "$INTERVAL"
    current="$(signature)"
    if [[ "$current" != "$last" ]]; then
        # Espera a que el editor termine de escribir (guardados en varios pasos).
        sleep 0.3
        last="$(signature)"
        say "Cambio detectado."
        rebuild
    fi
    # Si cerraste el juego con Esc, se reabre en el siguiente cambio.
    if [[ -n "$game_pid" ]] && ! kill -0 "$game_pid" 2>/dev/null; then
        wait "$game_pid" 2>/dev/null
        game_pid=""
        say "Juego cerrado. Se reabrirá al guardar un cambio."
    fi
done
