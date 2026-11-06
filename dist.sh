#!/usr/bin/env bash
# Genera el zip para jugadores del sistema actual, listo para descomprimir y jugar:
#   dist/linux/Vaquera2D-<versión>-linux.zip      (al correrlo en Linux)
#   dist/windows/Vaquera2D-<versión>-windows.zip  (al correrlo en MSYS2 UCRT64)
#
#   ./dist.sh    Pregunta la versión, prueba, compila y reemplaza el zip anterior.
#
# Si algo falla, el zip anterior se queda como estaba. Las partidas no viajan en
# el zip: el juego las guarda en la carpeta de datos de cada usuario.
set -euo pipefail
cd "$(dirname "$0")"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

case "$(uname -s)" in
    MINGW*|MSYS*) PLATFORM=windows; EXE=Vaquera2D.exe ;;
    *)            PLATFORM=linux;   EXE=Vaquera2D ;;
esac

while true; do
    read -r -p "Versión a generar (ej.: 0.3.0): " VERSION || fail "no se recibió ninguna versión"
    [[ $VERSION =~ ^[0-9A-Za-z][0-9A-Za-z._-]*$ ]] && break
    echo "Usa solo letras, números, punto, guion o guion bajo, sin espacios."
done

# El zip no debe salir con la prueba que regala las duales desde el nivel 1.
grep -Eq '^#define[[:space:]]+DUALS_FROM_ANY_LEVEL[[:space:]]+0([[:space:]]|$)' src/config.h \
    || fail "DUALS_FROM_ANY_LEVEL no está en 0 en src/config.h"

step "Revisando carpetas de distribución"
for folder in dist/linux dist/windows; do
    if [[ -d $folder ]]; then
        echo "$folder ya existe"
    else
        mkdir -p "$folder"
        echo "$folder creada"
    fi
done

OUT_DIR="dist/$PLATFORM"
NAME="Vaquera2D-$VERSION-$PLATFORM"
shopt -s nullglob
OLD=("$OUT_DIR"/Vaquera2D-*.zip)
shopt -u nullglob
if ((${#OLD[@]})); then
    printf 'Se reemplazará al terminar: %s\n' "${OLD[@]}"
else
    echo "No hay distribuibles en $OUT_DIR: se creará el primero"
fi

step "Pruebas y compilación normal (build.sh)"
./build.sh

step "Compilando la versión para distribuir"
RELEASE=build/release
LINK=-s
if [[ $PLATFORM == linux ]]; then
    # lib/ junto al ejecutable. DT_RPATH (no RUNPATH) también aplica a las
    # dependencias de las bibliotecas. make convierte $$ en $ y \ protege del shell.
    LINK='-s -Wl,--disable-new-dtags,-rpath,\$$ORIGIN/lib'
else
    # MSYS2's login profile points TMPDIR at its installation (see build.sh).
    mkdir -p build/tmp
    export TMPDIR="$PWD/build/tmp"
fi
# -fno-math-errno: sin esto, sqrtf pide la glibc más reciente y el juego no abre
# en distribuciones un poco más viejas que la máquina donde se compiló.
CFLAGS='-O2 -fno-math-errno' LDFLAGS="$LINK" \
    make -j"$(nproc 2>/dev/null || echo 2)" BUILD="$RELEASE" GEN=build/generated

step "Armando el contenido del zip"
PACKAGE=build/package
STAGE="$PACKAGE/$NAME"
trap 'rm -rf "$PACKAGE"' EXIT
rm -rf "$PACKAGE"
mkdir -p "$STAGE"
cp "$RELEASE/bin/$EXE" "$STAGE/"

# Lo que debe venir del sistema del jugador: glibc y compilador (no se pueden
# mezclar), y lo atado a su video y sonido, que todo escritorio ya trae.
SYSTEM_LIBS='ld-linux[^.]*|linux-vdso|libc|libm|libmvec|libdl|libpthread|librt|libresolv|libutil'
SYSTEM_LIBS+='|libgcc_s|libstdc\+\+|libatomic|libGL|libEGL|libGLX|libOpenGL|libGLdispatch|libdrm|libgbm'
SYSTEM_LIBS+='|libX11|libX11-xcb|libXext|libXfixes|libXrender|libXau|libXdmcp|libxcb[^.]*|libwayland-[a-z]+'
SYSTEM_LIBS+='|libasound|libpulse|libdbus-1|libsystemd|libz|libexpat|libffi|libglib-2\.0|libpcre2-8'

# Sigue las dependencias directas desde el ejecutable y se detiene en las del sistema.
bundle_linux_libs() {
    local binary="$1" name arrow path rest file needed
    local -A location=() seen=()
    while read -r name arrow path rest; do
        [[ $arrow == "=>" ]] || continue
        [[ $path == /* ]] || fail "falta $name en esta máquina"
        location[$name]=$path
    done < <(ldd "$binary")

    local queue=("$binary")
    mkdir -p "$STAGE/lib"
    while ((${#queue[@]})); do
        file="${queue[0]}"
        queue=("${queue[@]:1}")
        while read -r needed; do
            [[ -n $needed && -z ${seen[$needed]:-} ]] || continue
            seen[$needed]=1
            [[ $needed =~ ^($SYSTEM_LIBS)\.so ]] && continue
            [[ -n ${location[$needed]:-} ]] || fail "no se encontró $needed"
            cp -L "${location[$needed]}" "$STAGE/lib/$needed"
            chmod 644 "$STAGE/lib/$needed"
            queue+=("${location[$needed]}")
        done < <(readelf -d "$file" | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p')
    done
}

if [[ $PLATFORM == linux ]]; then
    bundle_linux_libs "$RELEASE/bin/$EXE"
    ldd "$STAGE/$EXE" | grep -q "$STAGE/lib/libSDL2-2.0" \
        || fail "el ejecutable no toma SDL2 de su carpeta lib/"
    MIN_GLIBC="$(objdump -T "$STAGE/$EXE" "$STAGE"/lib/* | grep -oE 'GLIBC_[0-9]+\.[0-9]+' \
        | sort -Vu | tail -n 1 || true)"
else
    # Same DLL selection as build.sh: only the MSYS2 ones, never Windows' own.
    ldd "$STAGE/$EXE" | awk '$3 ~ /^\/ucrt64\// {print $3}' | sort -u | xargs -r cp -t "$STAGE/"
fi

step "Probando el contenido del zip sin los recursos del proyecto"
# Carpeta de datos vacía: esta prueba jamás debe ver ni tocar las partidas de quien compila.
TEST_DATA="$PWD/$PACKAGE/datos_de_prueba"
mkdir -p "$TEST_DATA"
TEST_ENV=(env -u LD_LIBRARY_PATH XDG_DATA_HOME="$TEST_DATA"
          SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy)
# En Windows, sin ucrt64 en PATH: las DLL tienen que salir de la carpeta del juego.
[[ $PLATFORM == windows ]] && TEST_ENV+=(PATH=/usr/bin)
ABS_EXE="$PWD/$STAGE/$EXE"
(cd "$PACKAGE" && "${TEST_ENV[@]}" "$ABS_EXE" --verify)
(cd "$PACKAGE" && "${TEST_ENV[@]}" "$ABS_EXE" --smoke-test)

step "Comprimiendo"
NEW_ZIP="$PACKAGE/$NAME.zip"
# Con Python porque build.sh ya lo exige en ambos sistemas; zip no viene en MSYS2.
python3 - "$PACKAGE" "$NAME" "$NEW_ZIP" <<'PY'
import sys
import zipfile
from pathlib import Path

parent, name, output = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted((parent / name).rglob('*')):
        if path.is_file():
            # write() keeps the Unix permissions: the game stays executable.
            archive.write(path, path.relative_to(parent).as_posix())
PY

if ((${#OLD[@]})); then
    rm -f "${OLD[@]}"
fi
mv "$NEW_ZIP" "$OUT_DIR/$NAME.zip"

step "Listo"
ls -lh "$OUT_DIR/$NAME.zip"
if [[ $PLATFORM == linux ]]; then
    echo "Requiere una distribución con ${MIN_GLIBC/_/ } o más reciente."
    echo "Falta el de Windows: corre ./dist.sh en MSYS2 UCRT64."
else
    echo "Falta el de Linux: corre ./dist.sh en Linux."
fi
