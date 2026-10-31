#ifndef TEST_H
#define TEST_H

/* Minimal test helpers: each test binary returns non-zero on failure. */
#include <stdio.h>

static int test_failures;

#define CHECK(cond)                                                          \
    do {                                                                     \
        if (!(cond)) {                                                       \
            fprintf(stderr, "  FALLO %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            test_failures++;                                                 \
        }                                                                    \
    } while (0)

#define CHECK_NEAR(a, b, eps) CHECK(((a) - (b)) < (eps) && ((b) - (a)) < (eps))

#define RUN(test_fn)                \
    do {                            \
        int before = test_failures; \
        test_fn();                  \
        printf("  %s %s\n", test_failures == before ? "ok   " : "FALLO", #test_fn); \
    } while (0)

#define TEST_EXIT() (test_failures ? 1 : 0)

#endif
