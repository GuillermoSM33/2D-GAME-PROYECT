/* Command-line entry point; application, game rules and engine are separate. */
#include <stdio.h>
#include <string.h>

/* SDL maps main to its platform entry point on Windows. */
#include <SDL.h>

#include "app/application.h"
#include "app/verify.h"

static void print_usage(const char *program)
{
    printf("Uso: %s [--verify] [--smoke-test] [--capturas DIR]\n"
           "  --verify         Validar los recursos incrustados sin abrir ventana\n"
           "  --smoke-test     Recorrido automático corto; termina con código 0 si todo va bien\n"
           "  --capturas DIR   Guardar cada pantalla (menús, pelea, muro, pausa) como BMP en DIR\n",
           program);
}

int main(int argc, char **argv)
{
    bool smoke = false;
    const char *capture_dir = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--verify") == 0) {
            return app_verify_assets();
        } else if (strcmp(argv[i], "--smoke-test") == 0) {
            smoke = true;
        } else if (strcmp(argv[i], "--capturas") == 0 && i + 1 < argc) {
            capture_dir = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Opción desconocida: %s\n", argv[i]);
            print_usage(argv[0]);
            return 2;
        }
    }
    return app_run(smoke, capture_dir);
}
