#include <math.h>
#include <stdio.h>
#include <string.h>
#include "game/camera.h"
#include "game/casefile.h"
#include "game/stage_run.h"
#include "test.h"

static StageRun run;
static Player player;
static Progress progress;

static void setup(void)
{
    progress_init(&progress);player_init(&player);
    run_start(&run,TRAIN_STAGE,player.x,false);
}

static void test_complete_train_layout_and_mandatory_entry(void)
{
    setup();
    CHECK(run.train.present && !run.train.inside && !run.train.complete);
    CHECK(TRAIN_ROOMS==15 && run.train.zombie_count==TRAIN_CREW && run.zombie_count==33+TRAIN_CREW);
    CHECK(run.zombie_count<=RUN_MAX_ZOMBIES && !run.train.tablet && !run.train.suit);
    bool seal=false;
    for (int i=0;i<run.terrain.count;i++) {
        Piece *box=&run.terrain.items[i];
        float share=(box->x-run.start_x)/(run.goal_x-run.start_x);
        if (box->kind==TERRAIN_CRATE && casefile_crate_clue(TRAIN_STAGE,share)>=0) seal=true;
    }
    CHECK(seal);
    for (int room=0;room<TRAIN_ROOMS;room++) {
        int k=run.train.first_zombie+room*2;
        for (int z=k;z<k+2;z++) {
            float local=run.zombies[z].x-run.train.left;
            CHECK((int)(local/(TRAIN_ROOM_W*SPRITE_SCALE))==room);
            CHECK(!run.zombies[z].awake && !train_zombie_visible(&run,z));
        }
    }
    run_place_player(&run,&player);
    CHECK(player.max_x<=run.train.left+40*SPRITE_SCALE);
    /* Explosives and a destroyed exterior sprite cannot bypass boarding. */
    for (int i=0;i<run.terrain.count;i++)run.terrain.items[i].spent=true;
    run_place_player(&run,&player);
    CHECK_NEAR(player.max_x,run.train.left+40*SPRITE_SCALE,.001f);
    player.x=player.max_x;
    CHECK(train_use(&run,&player) && run.train.inside);
    CHECK(train_room(&run,player.x)==0);
    CHECK(train_zombie_visible(&run,run.train.first_zombie));
    CHECK(!train_zombie_visible(&run,0));
}

static void test_parts_terminal_and_enemies_gate_the_exit(void)
{
    setup();run.train.inside=true;
    const int rooms[]={1,6,TRAIN_CARS};
    for (int part=0;part<3;part++) {
        CHECK(train_part_position(&run,part,&player.x));
        CHECK(train_room(&run,player.x)==rooms[part]);
        CHECK(train_use(&run,&player));
        CHECK(run.weapon_parts&(1u<<part));
        CHECK(train_part_near(&run,&player)==-1);
    }
    player.x=run.train.right-40*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && !run.train.complete);
    /* The terminal reads nothing until the tablet from car 01 is docked. */
    player.x=run.train.left+(TRAIN_ROOMS-.35f)*TRAIN_ROOM_W*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && !run.train.control_read);
    player.x=train_tablet_x(&run);
    CHECK(train_room(&run,player.x)==0 && train_use(&run,&player) && run.train.tablet);
    player.x=run.train.left+(TRAIN_ROOMS-.35f)*TRAIN_ROOM_W*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && run.train.control_read);
    player.x=run.train.right-40*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && !run.train.complete);
    for (int k=run.train.first_zombie;k<run.train.first_zombie+run.train.zombie_count;k++)
        zombie_hit(&run.zombies[k],1e8f);
    CHECK(train_zombies_clear(&run));
    CHECK(train_use(&run,&player) && run.train.complete && !run.train.inside);
    CHECK(player.x>run.train.right);
    run_place_player(&run,&player);
    CHECK(player.max_x>player.x);
}

static void test_leaving_the_train_does_not_freeze_death_or_mission_completion(void)
{
    setup();
    run.train.inside=true;run.train.control_read=true;run.train.tablet=true;run.weapon_parts=7;
    for (int k=0;k<run.zombie_count;k++)zombie_hit(&run.zombies[k],1e8f);
    player.x=run.train.right-40*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && run.train.complete);
    /* Death animations must finish after changing back to the exterior. */
    for (int tick=0;tick<1500 && run.mission_chest<0;tick++) {
        player.health=player.max_health;
        run_update(&run,&player,&progress,FIXED_DT);
    }
    CHECK(run.defeated==run.zombie_count && run.mission_chest>=0);
    player.x=run.goal_x;
    for (int tick=0;tick<180 && run.phase==RUN_FIGHTING;tick++)run_update(&run,&player,&progress,FIXED_DT);
    CHECK(run.phase==RUN_CLEARED);
}

static void test_walk_every_room_with_real_player_movement(void)
{
    setup();
    player.x=run.train.left+40*SPRITE_SCALE;
    CHECK(train_use(&run,&player) && run.train.inside);
    InputState input;input_init(&input);
    unsigned visited=0;
    for (int tick=0;tick<20000 && run.train.inside;tick++) {
        int room=train_room(&run,player.x);
        visited|=1u<<room;
        if (fabsf(player.x-train_suit_x(&run))>32*SPRITE_SCALE || !run.train.suit)
            train_use(&run,&player);
        run_place_player(&run,&player);
        bool down[ACTION_COUNT]={0};down[ACTION_RIGHT]=true;
        input_update(&input,down);
        player_update(&player,&input,FIXED_DT);
        player.health=player.max_health;
        /* Combat is covered separately; defeat only enemies that have
         * actually woken in the same room/route as the moving character. */
        for (int k=0;k<run.zombie_count;k++)
            if (train_zombie_visible(&run,k) && run.zombies[k].awake)
                zombie_hit(&run.zombies[k],1e8f);
        run_update(&run,&player,&progress,FIXED_DT);
    }
    CHECK(visited==(1u<<TRAIN_ROOMS)-1);
    CHECK(run.train.complete && !run.train.inside && run.train.control_read);
    CHECK((run.weapon_parts&7)==7 && player.x>run.train.right);
    CHECK(run.train.tablet && !run.train.suit); /* The suit stays in the hatch's airlock */
}

static void test_the_suit_keeps_out_the_fumes_of_the_broken_tanks(void)
{
    setup();run.train.inside=true;
    CHECK(train_room_toxic(2) && train_room_toxic(6) && !train_room_toxic(0) && !train_room_toxic(13));
    player_set_stats(&player,1,100,0.0f,true);
    player.x=train_room_left(&run,2)+TRAIN_ROOM_W*SPRITE_SCALE*.5f;
    CHECK(train_in_fumes(&run,&player));
    int before=player.health;
    for (int tick=0;tick<(int)(3.05f/FIXED_DT);tick++) train_update(&run,&player,FIXED_DT);
    CHECK(player.health==before-3*(int)ceilf(100*TRAIN_FUMES_SHARE)); /* One breath a second, no armor */
    /* The suit, from its hooks in car 01: no more harm, in either car. */
    TrainPromptKind kind;
    player.x=train_suit_x(&run);
    const char *line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_USE && strstr(line,"TRAJE"));
    CHECK(train_use(&run,&player) && run.train.suit);
    for (int room=2;room<=6;room+=4) {
        player.x=train_room_left(&run,room)+TRAIN_ROOM_W*SPRITE_SCALE*.5f;
        before=player.health;
        CHECK(!train_in_fumes(&run,&player));
        for (int tick=0;tick<(int)(5.0f/FIXED_DT);tick++) train_update(&run,&player,FIXED_DT);
        CHECK(player.health==before);
    }
    /* Off again at the hooks; leaving by car 01's door leaves it there too. */
    player.x=train_suit_x(&run);
    CHECK(train_use(&run,&player) && !run.train.suit);
    CHECK(train_use(&run,&player) && run.train.suit);
    player.x=train_entry_x(&run);
    line=train_prompt(&run,&player,&kind);
    CHECK(line && strstr(line,"TRAJE"));
    CHECK(train_use(&run,&player) && !run.train.inside && !run.train.suit);
    /* Never outside the train. */
    player.x=train_room_left(&run,2);
    CHECK(!train_in_fumes(&run,&player));
}

static void test_the_tablet_is_the_first_goal_and_the_terminal_key(void)
{
    setup();run.train.inside=true;
    float at;
    player.x=train_entry_x(&run);
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_TABLET && fabsf(at-train_tablet_x(&run))<.01f);
    TrainPromptKind kind;
    player.x=train_terminal_x(&run);
    const char *line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_BLOCKED && strstr(line,"TABLETA"));
    player.x=train_tablet_x(&run);
    line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_USE && strstr(line,"TABLETA"));
    CHECK(train_use(&run,&player) && run.train.tablet);
    CHECK(train_prompt(&run,&player,&kind)==NULL || !strstr(train_prompt(&run,&player,&kind),"TOMAR"));
    player.x=train_terminal_x(&run);
    line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_USE && strstr(line,"ARCHIVO 4"));
    /* Hooks, tablet and door stand apart: each prompt has its own place. */
    CHECK(fabsf(train_suit_x(&run)-train_entry_x(&run))>64*SPRITE_SCALE);
    CHECK(fabsf(train_tablet_x(&run)-train_suit_x(&run))>64*SPRITE_SCALE);
}

static void test_all_eight_parts_are_reachable_across_later_missions(void)
{
    unsigned parts=TRAIN_PART_MASK;
    for (int stage=8;stage<=9;stage++) {
        player_init(&player);run_start(&run,stage,player.x,false);
        run.weapon_parts=parts;
        for (int part=3;part<8;part++) {
            float at;
            if (!train_part_position(&run,part,&at)) continue;
            CHECK(at>run.start_x && at<run.goal_x);
            bool spent[TERRAIN_MAX];
            for (int i=0;i<run.terrain.count;i++) { spent[i]=run.terrain.items[i].spent;run.terrain.items[i].spent=true; }
            float after;
            CHECK(train_part_position(&run,part,&after));
            CHECK_NEAR(after,at,.001f); /* Blowing a barrier cannot move a research item. */
            for (int i=0;i<run.terrain.count;i++)run.terrain.items[i].spent=spent[i];
            player.x=at;
            run_place_player(&run,&player);
            CHECK(player.x>=player.min_x && player.x<=player.max_x);
            CHECK(train_part_near(&run,&player)==part && train_use(&run,&player));
        }
        parts=run.weapon_parts;
    }
    CHECK(parts==255 && train_part_count(parts)==8);
}

static void kill_crew(void)
{
    for (int k=run.train.first_zombie;k<run.train.first_zombie+run.train.zombie_count;k++)
        zombie_hit(&run.zombies[k],1e8f);
}

static void test_prompts_name_what_is_missing_and_offer_e_only_when_it_acts(void)
{
    setup();
    TrainPromptKind kind;
    player.x=train_entry_x(&run);
    CHECK(train_prompt(&run,&player,&kind)!=NULL);
    CHECK(kind==(run_fight_left(&run)>0 ? TRAIN_PROMPT_BLOCKED : TRAIN_PROMPT_USE));
    run.train.inside=true;
    player.x=train_exit_x(&run);
    const char *line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_BLOCKED && strstr(line,"ARCHIVO 4"));
    run.train.control_read=true;
    line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_BLOCKED && strstr(line,"3 PIEZAS"));
    run.weapon_parts=TRAIN_PART_MASK;
    line=train_prompt(&run,&player,&kind);
    char crew[32];snprintf(crew,sizeof(crew),"%d INFECTADOS",TRAIN_CREW);
    CHECK(line && kind==TRAIN_PROMPT_BLOCKED && strstr(line,crew));
    CHECK(!train_exit_open(&run));
    kill_crew();
    line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_USE && train_exit_open(&run));
    player.x=train_terminal_x(&run);
    CHECK(train_prompt(&run,&player,&kind) && kind==TRAIN_PROMPT_DONE);
    float at;
    CHECK(train_part_position(&run,0,&at));
    run.weapon_parts=0;player.x=at;
    line=train_prompt(&run,&player,&kind);
    CHECK(line && kind==TRAIN_PROMPT_USE && strstr(line,train_part_name(0)));
}

static void test_inside_the_view_never_passes_the_ends_of_the_cars(void)
{
    setup();
    run.train.inside=true;
    for (float x=run.train.left;x<=run.train.right;x+=37*SPRITE_SCALE) {
        float left=train_camera(&run,camera_left(x));
        CHECK(left>=run.train.left-.01f && left+VIEW_WIDTH<=run.train.right+.01f);
    }
    run.train.inside=false;
    CHECK_NEAR(train_camera(&run,1234.0f),1234.0f,.001f);
}

static void test_next_goal_follows_the_mission_and_prefers_what_is_closer(void)
{
    setup();
    float at;
    player.x=train_entry_x(&run)-600;
    TrainGoal goal=train_next_goal(&run,&player,&at);
    CHECK((goal==TRAIN_GOAL_BOARD || goal==TRAIN_GOAL_YARD) && fabsf(at-train_entry_x(&run))<.01f);
    run.train.inside=true;player.x=train_entry_x(&run);run.train.tablet=true;
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_PART && train_room(&run,at)==1);
    run.weapon_parts=TRAIN_PART_MASK;
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_TERMINAL && fabsf(at-train_terminal_x(&run))<.01f);
    run.train.control_read=true;
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_CREW);
    kill_crew();
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_EXIT && fabsf(at-train_exit_x(&run))<.01f);
    /* At the terminal with a part left behind: read it first. */
    setup();run.train.inside=true;run.weapon_parts=3;run.train.tablet=true;
    player.x=train_terminal_x(&run);
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_TERMINAL);
    run.train.control_read=true;
    CHECK(train_next_goal(&run,&player,&at)==TRAIN_GOAL_PART && train_room(&run,at)==TRAIN_CARS);
}

static void test_the_map_counts_the_crew_room_by_room(void)
{
    setup();
    for (int room=0;room<TRAIN_ROOMS;room++) CHECK(train_crew_in_room(&run,room)==2);
    CHECK(train_crew_left(&run)==TRAIN_CREW);
    zombie_hit(&run.zombies[run.train.first_zombie+4],1e8f);
    CHECK(train_crew_in_room(&run,2)==1 && train_crew_left(&run)==TRAIN_CREW-1);
    for (int part=0;part<TRAIN_PARTS_ABOARD;part++) {
        float at;
        CHECK(train_part_position(&run,part,&at));
        run.train.inside=true;
        CHECK(train_room(&run,at)==train_part_room(part));
    }
    CHECK(train_part_room(TRAIN_PARTS_ABOARD)==-1);
}

static void test_supplies_use_the_clear_furniture_bays(void)
{
    setup();
    int supplies=0;
    for (int i=0;i<run.terrain.count;i++) {
        const Piece *box=&run.terrain.items[i];
        if (box->kind!=TERRAIN_CRATE || box->x<run.train.left || box->x>=run.train.right) continue;
        int room=(int)((box->x-run.train.left)/(TRAIN_ROOM_W*SPRITE_SCALE));
        int bay=train_supply_art(room);
        CHECK(bay>=0);
        float expected=train_room_left(&run,room)+bay*SPRITE_SCALE;
        CHECK_NEAR(box->x,expected,.01f);
        for (int part=0;part<TRAIN_PARTS_ABOARD;part++) {
            float where;
            CHECK(train_part_position(&run,part,&where));
            CHECK(fabsf(box->x-where)>48*SPRITE_SCALE);
        }
        supplies++;
    }
    CHECK(supplies==7); /* Six supply cars and the container-seal clue. */
    CHECK(train_supply_art(0)==-1 && train_supply_art(TRAIN_ROOMS-1)==-1);
}

int main(void)
{
    RUN(test_complete_train_layout_and_mandatory_entry);
    RUN(test_parts_terminal_and_enemies_gate_the_exit);
    RUN(test_leaving_the_train_does_not_freeze_death_or_mission_completion);
    RUN(test_walk_every_room_with_real_player_movement);
    RUN(test_all_eight_parts_are_reachable_across_later_missions);
    RUN(test_prompts_name_what_is_missing_and_offer_e_only_when_it_acts);
    RUN(test_inside_the_view_never_passes_the_ends_of_the_cars);
    RUN(test_next_goal_follows_the_mission_and_prefers_what_is_closer);
    RUN(test_the_map_counts_the_crew_room_by_room);
    RUN(test_the_suit_keeps_out_the_fumes_of_the_broken_tanks);
    RUN(test_the_tablet_is_the_first_goal_and_the_terminal_key);
    RUN(test_supplies_use_the_clear_furniture_bays);
    return TEST_EXIT();
}
