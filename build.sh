#!/usr/bin/env bash
# Compila Vaquera 2D y deja el ejecutable final en dist/.
#   ./build.sh           Compilación incremental
#   ./build.sh --clean   Compilación desde cero
# Si alguna prueba falla, se detiene y dist/ no se modifica.
set -euo pipefail
cd "$(dirname "$0")"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

step "Comprobando herramientas"
for tool in cc make pkg-config python3; do
    command -v "$tool" >/dev/null || fail "falta '$tool'. Instala: sudo apt install build-essential pkg-config python3"
done
pkg-config --exists sdl2 SDL2_ttf \
    || fail "faltan SDL2/SDL2_ttf. Instala: sudo apt install libsdl2-dev libsdl2-ttf-dev"
echo "SDL2 $(pkg-config --modversion sdl2), SDL2_ttf $(pkg-config --modversion SDL2_ttf)"

if [[ "${1:-}" == "--clean" ]]; then
    step "Limpiando build/"
    make clean
fi

JOBS="$(nproc 2>/dev/null || echo 2)"

step "Pruebas de lógica"
make -j"$JOBS" test

step "Compilando"
make -j"$JOBS"

step "Verificando recursos incrustados"
./build/bin/Vaquera2D --verify

step "Prueba de humo (sin ventana)"
SDL_VIDEODRIVER=dummy ./build/bin/Vaquera2D --smoke-test

step "Publicando en dist/"
mkdir -p dist
cp build/bin/Vaquera2D dist/Vaquera2D.tmp
mv dist/Vaquera2D.tmp dist/Vaquera2D
chmod +x dist/Vaquera2D
ls -lh dist/Vaquera2D

printf '\nListo. Ejecuta: ./dist/Vaquera2D\n'
