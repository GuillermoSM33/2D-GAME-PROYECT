#include "config.h"
#include "game/smoke.h"
#include "test.h"

static void test_puffs_leave_one_after_another(void)
{
    Smoke smoke;
    smoke_clear(&smoke);
    smoke_emit(&smoke, 500.0f, 300.0f, 1);
    CHECK(smoke_active_count(&smoke) == SMOKE_PUFFS_PER_SHOT);
    smoke_update(&smoke, FIXED_DT);
    int visible = 0;
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++)
        visible += puff_visible(&smoke.puffs[i]);
    CHECK(visible >= 1 && visible < SMOKE_PUFFS_PER_SHOT);
}

static void test_rises_drifts_grows_and_fades(void)
{
    Smoke smoke;
    smoke_clear(&smoke);
    smoke_emit(&smoke, 500.0f, 300.0f, 1);
    const Puff *p = &smoke.puffs[0];
    smoke_update(&smoke, FIXED_DT);
    int size0 = puff_size(p);
    float alpha0 = puff_opacity(p);
    for (int i = 0; i < 20; i++)
        smoke_update(&smoke, FIXED_DT);
    CHECK(p->active);
    CHECK(p->y < 300.0f - 10.0f); /* Rose */
    CHECK(p->x > 500.0f);         /* Drifted ahead */
    CHECK(puff_size(p) > size0);
    CHECK(puff_opacity(p) < alpha0);
}

static void test_drifts_toward_facing(void)
{
    Smoke smoke;
    smoke_clear(&smoke);
    smoke_emit(&smoke, 500.0f, 300.0f, -1);
    for (int i = 0; i < 20; i++)
        smoke_update(&smoke, FIXED_DT);
    CHECK(smoke.puffs[0].x < 500.0f);
}

static void test_cloud_clears_by_itself(void)
{
    Smoke smoke;
    smoke_clear(&smoke);
    smoke_emit(&smoke, 500.0f, 300.0f, 1);
    float longest = (SMOKE_PUFFS_PER_SHOT - 1) * SMOKE_PUFF_INTERVAL + SMOKE_PUFF_LIFE * 1.2f;
    for (float t = 0.0f; t < longest + 2.0f * FIXED_DT; t += FIXED_DT)
        smoke_update(&smoke, FIXED_DT);
    CHECK(smoke_active_count(&smoke) == 0);
}

static void test_many_shots_never_overflow(void)
{
    Smoke smoke;
    smoke_clear(&smoke);
    for (int shot = 0; shot < 20; shot++) {
        smoke_emit(&smoke, 500.0f, 300.0f, 1);
        smoke_update(&smoke, FIXED_DT);
    }
    CHECK(smoke_active_count(&smoke) == SMOKE_MAX_PUFFS);
    /* The newest cloud got its puffs: the last one is still waiting to appear. */
    int waiting = 0;
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++)
        waiting += smoke.puffs[i].active && !puff_visible(&smoke.puffs[i]);
    CHECK(waiting >= SMOKE_PUFFS_PER_SHOT - 2);
}

int main(void)
{
    printf("test_smoke\n");
    RUN(test_puffs_leave_one_after_another);
    RUN(test_rises_drifts_grows_and_fades);
    RUN(test_drifts_toward_facing);
    RUN(test_cloud_clears_by_itself);
    RUN(test_many_shots_never_overflow);
    return TEST_EXIT();
}
