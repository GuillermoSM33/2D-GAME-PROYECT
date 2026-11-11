# THE MIRACLE

(Antes Vaquera 2D; el repo y la carpeta del proyecto conservan el nombre viejo.)

**Cambio pendiente en la PC de Windows:** desde 2026-11-11 las partidas y preferencias van en
`%APPDATA%\TheMiracle\TheMiracle\` (antes `%APPDATA%\Vaquera2D\Vaquera2D\`). Al abrir este repo
en Windows, si aún existe la carpeta vieja y no la nueva, muévela (en PowerShell:
`New-Item -ItemType Directory -Force "$env:APPDATA\TheMiracle" | Out-Null; Move-Item "$env:APPDATA\Vaquera2D\Vaquera2D" "$env:APPDATA\TheMiracle\TheMiracle"`;
luego borra `%APPDATA%\Vaquera2D` si quedó vacía) y quita este aviso. En Linux ya se hizo.
La historia, sus nombres y las fases están en `docs/LORE.md`: respétalo. El arte de las
cinemáticas sale de `tools/make_cinematics.py`. **Sin voces:** la
historia se cuenta solo con cinemáticas, ruidos y texto.

Juego 2D en C11 + SDL2/SDL2_ttf con motor propio (`src/engine`), lógica en `src/game`,
pruebas en `tests/`. Los recursos se incrustan al compilar con `tools/embed_assets.py`.
Documentación en `README.md` y `docs/`; dónde va cada recurso y cómo se nombra:
`docs/ASSETS.md` (respétalo al agregar sprites, fondos o sonidos).

## Directriz principal: Windows y Linux

**El juego debe compilar y funcionar siempre en Windows y en Linux.** Todo cambio (código,
`Makefile`, `build.sh`, `tools/`, recursos, docs) tiene que funcionar en ambos.

- Nada de APIs, rutas ni comandos propios de un solo sistema sin cubrir el otro; lo que
  dependa del sistema va por SDL.
- Scripts en POSIX `sh`/`bash` y con finales de línea **LF** (con CRLF dejan de funcionar).
- No agregar dependencias que no existan tanto en apt (Ubuntu/Debian) como en MSYS2 UCRT64.
- Después de un cambio, corre `./build.sh` en la máquina actual y avisa qué falta probar en
  el otro sistema.

## Dependencias

SDL2, SDL2_ttf y **SDL2_mixer** (audio).
Si al bajar cambios `build.sh` dice que falta SDL2_mixer:

- **Linux:** `sudo apt install libsdl2-mixer-dev`
- **Windows (MSYS2 UCRT64):** `pacman -S mingw-w64-ucrt-x86_64-SDL2_mixer`

Solo para `tools/crush_sfx.py` (grabar/convertir sonidos, no para compilar): **ffmpeg**
(`sudo apt install ffmpeg` / `pacman -S mingw-w64-ucrt-x86_64-ffmpeg`).

## Compilar

- **Linux:** `./build.sh` (requisitos en `README.md`).
- **Windows:** MSYS2 en `C:\msys64`, entorno UCRT64. Desde una terminal MSYS2 UCRT64:
  `./build.sh`. Desde PowerShell:
  `$env:MSYSTEM="UCRT64"; $env:CHERE_INVOKING="1"; C:\msys64\usr\bin\bash.exe --login -c "./build.sh"`
- En ambos sistemas sirven `make`, `make test`, `make run` y `make watch`.
- **Zip para jugadores:** `./dist.sh` pide la versión y deja el zip del sistema actual en
  `dist/linux/` o `dist/windows/`.

## Arte de la vaquera

El usuario lo aprobó el 2026-11-05: consérvalo así salvo que pida cambios. Tiene **un solo cuerpo**
en todas las poses de pie: torso y cinturón salen de las tablas de `tools/rework_cowgirl.py`
(`TORSO_FRONT`, `BELT_FRONT`, `BACK_SIDE`), relativas a la hebilla, que va bajo su barbilla. Cámbialo
ahí, nunca en una sola hoja. La meta es una silueta de reloj de arena: hombros y cadera de ancho
parecido, cintura marcada y sin escalón entre cinturón y pierna; la curva va en tramos de dos filas
para que no salga en escalera.
Sus brazos no vienen de la plantilla: se dibujan aparte sobre el cuerpo completo, con un solo modelo
de brazo y guante (`tools/cowgirl_arm.py`) y **un solo dibujo de pistola**,
`assets/sprites/characters/cowgirl/weapons/pistol.png`, para las dos manos; las poses están en `walk_arms`, `jump_arms`
y `ON_HIPS`. Al caminar se balancean los dos, casi rectos y con aire junto a la cintura; solo parada
lleva las manos en la cadera.
Regenera todas sus hojas con
`python3 tools/rebuild_cowgirl.py` y revísalas ampliadas antes de reportarlas.

`DUALS_FROM_ANY_LEVEL` en `src/config.h` está en 0; ponlo en 1 solo para probar las duales desde el nivel 1.

## Repositorio

https://github.com/GuillermoSM33/2D-GAME-PROYECT, en la cuenta **personal** del usuario
(GuillermoSM33). No uses la cuenta del trabajo. El usuario escribe en español.
