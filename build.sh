#!/usr/bin/env bash
# Compila THE MIRACLE y deja el ejecutable final en dist/.
#   ./build.sh           Compilación incremental
#   ./build.sh --clean   Compilación desde cero
# Si alguna prueba falla, se detiene y dist/ no se modifica.
set -euo pipefail
cd "$(dirname "$0")"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

case "$(uname -s)" in
    MINGW*|MSYS*) WINDOWS=1; EXE=TheMiracle.exe ;;
    *)            WINDOWS=0; EXE=TheMiracle ;;
esac

step "Comprobando herramientas"
for tool in cc make pkg-config python3; do
    command -v "$tool" >/dev/null && continue
    if [[ $WINDOWS == 1 ]]; then
        fail "falta '$tool'. En MSYS2 UCRT64 instala: pacman -S --needed make mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-pkgconf mingw-w64-ucrt-x86_64-python"
    fi
    fail "falta '$tool'. Instala: sudo apt install build-essential pkg-config python3"
done
for lib in sdl2 SDL2_ttf SDL2_mixer; do
    pkg-config --exists "$lib" && continue
    if [[ $WINDOWS == 1 ]]; then
        fail "falta $lib. Instala (MSYS2 UCRT64): pacman -S mingw-w64-ucrt-x86_64-SDL2 mingw-w64-ucrt-x86_64-SDL2_ttf mingw-w64-ucrt-x86_64-SDL2_mixer"
    fi
    fail "falta $lib. Instala: sudo apt install libsdl2-dev libsdl2-ttf-dev libsdl2-mixer-dev"
done
echo "SDL2 $(pkg-config --modversion sdl2), SDL2_ttf $(pkg-config --modversion SDL2_ttf)," \
     "SDL2_mixer $(pkg-config --modversion SDL2_mixer)"

step "Comprobando arquitectura"
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_architecture.py

step "Comprobando sonidos y originales protegidos"
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_audio.py

step "Comprobando sprites de las familias y originales protegidos"
PYTHONDONTWRITEBYTECODE=1 python3 tools/make_zombies.py --verify

step "Comprobando el arte de UI, objetos y reparto de apoyo"
PYTHONDONTWRITEBYTECODE=1 python3 tools/rebuild_support_art.py --verify

step "Comprobando el arte de las cinemáticas"
PYTHONDONTWRITEBYTECODE=1 python3 tools/make_cinematics.py --only lab ambulance --verify

if [[ "${1:-}" == "--clean" ]]; then
    step "Limpiando build/"
    make clean
fi

if [[ $WINDOWS == 1 ]]; then
    # MSYS2's login profile points TMPDIR at its installation. Keep compiler
    # scratch files alongside the build so ordinary workspace access is enough.
    mkdir -p build/tmp
    export TMPDIR="$PWD/build/tmp"
fi

JOBS="$(nproc 2>/dev/null || echo 2)"

step "Pruebas de lógica"
make -j"$JOBS" test

step "Compilando"
make -j"$JOBS"

step "Verificando recursos incrustados"
"./build/bin/$EXE" --verify

step "Prueba de humo (sin ventana)"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "./build/bin/$EXE" --smoke-test

step "Publicando en dist/"
mkdir -p dist
cp "build/bin/$EXE" "dist/$EXE.tmp"
mv "dist/$EXE.tmp" "dist/$EXE"
chmod +x "dist/$EXE"
if [[ $WINDOWS == 1 ]]; then
    # So the .exe runs on double-click: copy the MSYS2 DLLs it needs next to it.
    ldd "build/bin/$EXE" | awk '$3 ~ /^\/ucrt64\// {print $3}' | sort -u |
        while IFS= read -r dll; do cp "$dll" dist/; done
    echo "$(ls dist/*.dll | wc -l) DLL(s) junto al ejecutable"
fi
ls -lh "dist/$EXE"

printf '\nListo. Ejecuta: ./dist/%s\n' "$EXE"
