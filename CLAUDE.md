# Vaquera 2D

Juego 2D en C11 + SDL2/SDL2_ttf con motor propio (`src/engine`), lógica en `src/game`,
pruebas en `tests/`. Los recursos se incrustan al compilar con `tools/embed_assets.py`.
Documentación en `README.md` y `docs/`.

## Directriz principal: Windows y Linux

**El juego debe compilar y funcionar siempre en Windows y en Linux.** Todo cambio (código,
`Makefile`, `build.sh`, `tools/`, recursos, docs) tiene que funcionar en ambos.

- Nada de APIs, rutas ni comandos propios de un solo sistema sin cubrir el otro; lo que
  dependa del sistema va por SDL.
- Scripts en POSIX `sh`/`bash` y con finales de línea **LF** (con CRLF dejan de funcionar).
- No agregar dependencias que no existan tanto en apt (Ubuntu/Debian) como en MSYS2 UCRT64.
- Después de un cambio, corre `./build.sh` en la máquina actual y avisa qué falta probar en
  el otro sistema.

## Compilar

- **Linux:** `./build.sh` (requisitos en `README.md`).
- **Windows:** MSYS2 en `C:\msys64`, entorno UCRT64. Desde una terminal MSYS2 UCRT64:
  `./build.sh`. Desde PowerShell:
  `$env:MSYSTEM="UCRT64"; $env:CHERE_INVOKING="1"; C:\msys64\usr\bin\bash.exe --login -c "./build.sh"`
- En ambos sistemas sirven `make`, `make test`, `make run` y `make watch`.

## Repositorio

https://github.com/GuillermoSM33/2D-GAME-PROYECT, en la cuenta **personal** del usuario
(GuillermoSM33). No uses la cuenta del trabajo. El usuario escribe en español.
