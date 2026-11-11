#include <string.h>

#include "config.h"
#include "game/casefile.h"

/* Case 0, "La paciente cero": how it reached Ojo de Cuervo (1-1 and 1-2).
 * Case 1, "MRC-2": what it is and why the dead get up (1-3).
 * Case 2, "Las cintas": someone inside Vantrell (1-4).
 * Case 3, "El científico": who (1-5). */
const ClueDef CLUES[CLUE_COUNT] = {
    {"Orden de traslado",
     "Ambulancia 3. Mujer de unos 30 años, *herida de bala* en el costado. Recogida en la carretera "
     "9, km 41: *zona restringida de Vantrell*. Destino: hospital de Ojo de Cuervo.",
     "Formulario de la ambulancia 3. En la casilla de origen alguien tachó *\"Laboratorio 4\"* y escribió encima \"carretera 9\". Quien llenó el formulario sabía de dónde venía la herida.",
     CLUE_DOCUMENT, 0, 0, CLUE_FROM_MISSION, 0.0f, 0},
    {"Credencial de prensa",
     "*VALERIA ORTIZ*, prensa. La foto está manchada de sangre seca; alguien la arrancó de un chaleco.",
     "Plástico rayado, con el logo de un diario de la capital. En la foto, Valeria sonríe. Al reverso, escrito con pluma: *\"Si me pasa algo, busquen a N.\"*",
     CLUE_OBJECT, 0, 0, CLUE_FROM_CRATE, 0.46f, 0},
    {"Cinta 1",
     "[Estática] ...si alguien encuentra esto: *Laboratorio 4*. Lo que hacen aquí *no es una cura*. "
     "Lo están escondiendo... [se corta]",
     "Casete de 60 minutos con la etiqueta \"LAB 4 - 1\". Casi todo es estática. Entre el ruido se oyen una alarma y pasos que corren. La voz es de una mujer joven, y *está asustada*.",
     CLUE_TAPE, 0, 0, CLUE_FROM_ZOMBIE, 0.0f, 3},
    {"Registro de ingreso",
     "03:58. Herida de bala. *41 grados* de fiebre en una hora. La atienden el doctor Ruiz y la "
     "enfermera Salas, *sin guantes*: no había tiempo.",
     "Libro de ingresos del hospital. La entrada de las 03:58 está escrita con prisa, en tinta roja. Debajo hay *diez ingresos más en dos horas*, todos con la misma nota: fiebre, venas negras.",
     CLUE_DOCUMENT, 0, 1, CLUE_FROM_MISSION, 0.0f, 0},
    {"Foto del pasillo",
     "Camillas en el pasillo del hospital. Todos los pacientes tienen la misma marca: *venas negras* "
     "en el cuello.",
     "Foto instantánea tomada con flash. Al fondo, una enfermera con cubrebocas mira a la cámara. En una camilla, una mano asoma de la sábana: tiene *las venas negras hasta los dedos*.",
     CLUE_PHOTO, 0, 1, CLUE_FROM_CRATE, 0.6f, 0},
    {"Hoja clínica",
     "Paciente sin nombre. Muerte clínica a las *06:10*. A las *06:24*, la paciente se levanta. "
     "Nadie firmó su alta.",
     "Hoja de signos vitales. El pulso cae a cero a las 06:10 y la línea sigue plana catorce minutos. A las 06:24, *el trazo vuelve a saltar*. Al margen, alguien escribió: \"Imposible.\"",
     CLUE_DOCUMENT, 0, 1, CLUE_FROM_ZOMBIE, 0.0f, 5},
    {"Memorándum de Vantrell",
     "Asunto: *MRC-1*. Mutación pasiva confirmada; revertir su evolución es imposible. "
     "Recomendación: recombinar su ADN con cepas frágiles.",
     "Memorándum con sello de CONFIDENCIAL, dirigido a *Julian Vantrell*, director de la compañía. Lo firma la jefa del proyecto con sus iniciales. Al pie: \"Destruir después de leer.\"",
     CLUE_DOCUMENT, 1, 2, CLUE_FROM_MISSION, 0.0f, 0},
    {"Informe del día 94",
     "*MRC-2*, estable a los 30 días. Día 94: *reactivación*. Muta al doble de velocidad. Los "
     "órganos fallan, pero el cuerpo no se detiene.",
     "Gráfica de mutación de MRC-2. La curva se mantiene plana 93 días y el día 94 se dispara. Una nota a lápiz: *\"No lo contuvimos. Solo lo dormimos.\"*",
     CLUE_DOCUMENT, 1, 2, CLUE_FROM_ZOMBIE, 0.0f, 2},
    {"Muestra rota",
     "Un tubo partido con restos de líquido verde. Etiqueta: *MRC-2, LOTE 7*. Todavía brilla.",
     "Restos de un tubo de ensayo de Vantrell. El líquido verde *brilla en la oscuridad* y se mueve solo, como si buscara salir. El lote 7 es el que se rompió en el Laboratorio 4.",
     CLUE_OBJECT, 1, 2, CLUE_FROM_CRATE, 0.22f, 0},
    {"Cinta 2",
     "[Valeria] Mi fuente dice que el proyecto se paga con *dinero del gobierno*. Por eso nadie lo "
     "va a parar.",
     "Casete etiquetado \"LAB 4 - 2\". Valeria habla en voz baja, como si alguien pudiera oírla. Al final se oye otra voz, de hombre: *\"Ya no hay vuelta atrás, Vale.\"*",
     CLUE_TAPE, 2, 3, CLUE_FROM_ZOMBIE, 0.0f, 6},
    {"Cinta 3",
     "[Valeria] Me consiguió tarjetas de acceso y la hora del cambio de guardia. Firma sus notas con "
     "una sola letra: *N*.",
     "Casete etiquetado \"LAB 4 - 3\". Valeria repasa el plan: entrar a las 02:00, en el cambio de guardia, y salir antes de las 04:00. *Nunca salió por su propio pie.*",
     CLUE_TAPE, 2, 3, CLUE_FROM_MISSION, 0.0f, 0},
    {"Tarjeta de acceso",
     "*VANTRELL, NIVEL 4*. Alguien raspó el nombre con una navaja. Solo se lee la primera letra: *N*.",
     "Tarjeta magnética de nivel 4, la más alta del laboratorio. El chip todavía funciona. Las rayas de navaja son recientes: alguien quiso *borrar quién la usó*.",
     CLUE_OBJECT, 2, 3, CLUE_FROM_CRATE, 0.84f, 0},
    {"Bata quemada",
     "Una bata de laboratorio con un bordado en el pecho: *DR. E. NAVARRO*. La manga tiene "
     "quemaduras de plasma.",
     "Bata de laboratorio de talla mediana. En el bolsillo hay una pluma y un gafete sin foto. Las quemaduras de la manga son de plasma: *tuvo el prototipo en las manos*.",
     CLUE_OBJECT, 3, 4, CLUE_FROM_ZOMBIE, 0.0f, 8},
    {"Plano del prototipo",
     "*Cañón de plasma experimental*. Propiedad de Vantrell. Nota a mano: falta del inventario "
     "desde el día 14.",
     "Plano técnico del prototipo, sellado por Vantrell. El arma usa una celda de energía experimental. Una nota a mano en el margen: *\"Si cae en malas manos, que sean las mías.\"*",
     CLUE_DOCUMENT, 3, 4, CLUE_FROM_MISSION, 0.0f, 0},
    {"Foto vieja",
     "Dos estudiantes abrazados en la universidad. Al reverso: \"Perdóname, Vale. *E.*\"",
     "Una foto de hace diez años: Elías y Valeria con las togas de graduación. Él escribió al reverso, con la *misma letra* que firma las notas como N.",
     CLUE_PHOTO, 3, 4, CLUE_FROM_CRATE, 0.74f, 0},
};

const CaseDef CASES[CASE_COUNT] = {
    {"LA PACIENTE CERO", "¿Cómo llegó el brote a Ojo de Cuervo?",
     {"Por el agua del río", "En la herida de una mujer baleada", "Un camión de Vantrell lo regó"},
     1, "INFORME DE URGENCIAS, HOSPITAL DE OJO DE CUERVO",
     "03:58. Ingresa una mujer de unos treinta años con una herida de bala en el costado. La "
     "ambulancia la recogió en la carretera 9, kilómetro 41, dentro del perímetro restringido de "
     "Vantrell. Entre su ropa, una credencial de prensa: *Valeria Ortiz*.\n\n"
     "La atienden el doctor Ruiz y la enfermera Salas, sin guantes: no hubo tiempo. En una hora "
     "llega a 41 grados y le aparecen venas negras en el cuello. Muere a las 06:10. *A las 06:24 "
     "se incorpora en la camilla.*\n\n"
     "*Conclusión:* el brote no llegó por el agua ni por la carretera. Entró a Ojo de Cuervo *dentro "
     "de la herida de una paciente*."},
    {"MRC-2", "¿Por qué los muertos se levantan?",
     {"Un ritual en el panteón", "La mutación obliga al cuerpo a seguir", "Siguen vivos, solo enfermos"},
     1, "DOCUMENTOS INTERNOS DE VANTRELL PHARMACEUTICALS",
     "MRC-1 fue el primer intento de The Miracle: una bacteria diseñada por inteligencia "
     "artificial para blindar el cuerpo contra cualquier enfermedad. Un error en la mezcla de ADN "
     "le dio *mutación pasiva* y una coraza que impedía revertirla.\n\n"
     "Para contenerla, el equipo la recombinó con cepas frágiles. Así nació *MRC-2*, estable durante "
     "treinta días. *El día 94 se reactivó* y empezó a mutar al doble de velocidad.\n\n"
     "*Conclusión:* la mutación desgasta el metabolismo hasta que los órganos fallan, pero obliga al "
     "cuerpo a mantener funciones mínimas. *Por eso los muertos se levantan.*"},
    {"LAS CINTAS", "¿Quién ayudaba a Valeria desde dentro?",
     {"El director Julian Vantrell", "Un científico que firmaba con N", "Uno de los mercenarios"},
     1, "TRANSCRIPCIÓN DE LAS CINTAS DE VALERIA ORTIZ",
     "Valeria llevaba meses siguiendo a Vantrell. En la cinta 2, su fuente le confirma que el "
     "proyecto se paga con *dinero del gobierno*: nadie con poder piensa detenerlo.\n\n"
     "En la cinta 3 cuenta cómo pensaba entrar: tarjetas de acceso de nivel 4 y la hora exacta del "
     "cambio de guardia. Su contacto nunca firmó con su nombre, solo con una letra: *N*.\n\n"
     "*Conclusión:* Valeria no entró sola al Laboratorio 4. *Alguien de dentro le abrió las puertas.*"},
    {"EL CIENTÍFICO", "¿Quién se llevó el prototipo?",
     {"Un mercenario desertor", "El doctor Elías Navarro", "El sargento Reyes"},
     1, "EXPEDIENTE PERSONAL RECUPERADO",
     "*Dr. Elías Navarro*, investigador del Laboratorio 4. Fue de los primeros en ver lo que MRC-2 "
     "les hacía a los sujetos de prueba. Conocía a Valeria Ortiz desde la universidad.\n\n"
     "Fue él quien la llamó para sacar la verdad a la luz. La noche de la filtración desapareció, y "
     "con él faltó del inventario el *cañón de plasma experimental*.\n\n"
     "*Conclusión: N es Navarro.* Sigue vivo, está armado y sabe más de lo que nadie ha contado."},
};

void casefile_init(CaseFile *file)
{
    memset(file, 0, sizeof(*file));
}

bool casefile_has(const CaseFile *file, int clue)
{
    return clue >= 0 && clue < CLUE_COUNT && (file->found & (1u << clue)) != 0;
}

bool casefile_take(CaseFile *file, int clue)
{
    if (clue < 0 || clue >= CLUE_COUNT || casefile_has(file, clue))
        return false;
    file->found |= 1u << clue;
    return true;
}

int casefile_found_count(const CaseFile *file)
{
    int n = 0;
    for (int c = 0; c < CLUE_COUNT; c++)
        n += casefile_has(file, c);
    return n;
}

int casefile_case_clues(int case_index, int *out)
{
    int n = 0;
    for (int c = 0; c < CLUE_COUNT && n < CASE_MAX_CLUES; c++) {
        if (CLUES[c].case_index == case_index) {
            if (out)
                out[n] = c;
            n++;
        }
    }
    return n;
}

int casefile_case_found(const CaseFile *file, int case_index)
{
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(case_index, ids), found = 0;
    for (int k = 0; k < n; k++)
        found += casefile_has(file, ids[k]);
    return found;
}

bool casefile_solved(const CaseFile *file, int case_index)
{
    return case_index >= 0 && case_index < CASE_COUNT && (file->solved & (1u << case_index)) != 0;
}

bool casefile_ready(const CaseFile *file, int case_index)
{
    if (case_index < 0 || case_index >= CASE_COUNT || casefile_solved(file, case_index))
        return false;
    return casefile_case_found(file, case_index) == casefile_case_clues(case_index, NULL);
}

bool casefile_answer(CaseFile *file, int case_index, int option)
{
    if (!casefile_ready(file, case_index) || option != CASES[case_index].answer)
        return false;
    file->solved |= 1u << case_index;
    return true;
}

static int stage_clue(int stage, ClueSource source)
{
    for (int c = 0; c < CLUE_COUNT; c++)
        if (CLUES[c].stage == stage && CLUES[c].source == source)
            return c;
    return -1;
}

int casefile_mission_clue(int stage)
{
    return stage_clue(stage, CLUE_FROM_MISSION);
}

int casefile_zombie_clue(int stage, int zombie_index, int zombie_count)
{
    int c = stage_clue(stage, CLUE_FROM_ZOMBIE);
    if (c < 0 || zombie_count <= 0)
        return -1;
    /* A route shorter than the script's still has its clue: on its last zombie. */
    int carrier = CLUES[c].zombie < zombie_count ? CLUES[c].zombie : zombie_count - 1;
    return zombie_index == carrier ? c : -1;
}

/* How far from its spot a crate may stand and still hold the clue: a group
 * of crates spans a little of the road. */
#define CRATE_CLUE_REACH 0.025f

int casefile_crate_clue(int stage, float share)
{
    int c = stage_clue(stage, CLUE_FROM_CRATE);
    if (c < 0)
        return -1;
    float d = share - CLUES[c].at;
    return d > -CRATE_CLUE_REACH && d < CRATE_CLUE_REACH ? c : -1;
}

int casefile_stage_found(const CaseFile *file, int stage)
{
    int n = 0;
    for (int c = 0; c < CLUE_COUNT; c++)
        n += CLUES[c].stage == stage && casefile_has(file, c);
    return n;
}

/* ---- The board ---------------------------------------------------------------- */

int board_card_x(int col)
{
    return BOARD_X + BOARD_LABEL_W + col * BOARD_CARD_STEP;
}

int board_row_y(int row)
{
    return BOARD_Y + row * BOARD_ROW_H;
}

int board_slot_x(void)
{
    return board_card_x(CASE_MAX_CLUES) + 14;
}

void board_view_init(BoardView *view)
{
    memset(view, 0, sizeof(*view));
    view->revealed = -1;
    view->examined = -1;
}

int board_selected_clue(const BoardView *view)
{
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(view->row, ids);
    return view->col < n ? ids[view->col] : -1;
}

static bool inside(int x, int y, int left, int top, int w, int h)
{
    return x >= left && x < left + w && y >= top && y < top + h;
}

/* The card or slot under the pointer: its row and column, or false. */
static bool board_hit(int x, int y, int *row, int *col)
{
    for (int r = 0; r < CASE_COUNT; r++) {
        int top = board_row_y(r) + (BOARD_ROW_H - BOARD_CARD) / 2;
        int n = casefile_case_clues(r, NULL);
        for (int c = 0; c < n; c++) {
            if (inside(x, y, board_card_x(c), top, BOARD_CARD, BOARD_CARD)) {
                *row = r;
                *col = c;
                return true;
            }
        }
        if (inside(x, y, board_slot_x(), top, BOARD_SLOT_W, BOARD_CARD)) {
            *row = r;
            *col = n;
            return true;
        }
    }
    return false;
}

static int option_hit(int x, int y)
{
    for (int o = 0; o < CASE_OPTIONS; o++)
        if (inside(x, y, (WINDOW_WIDTH - BOARD_OPTION_W) / 2, BOARD_OPTION_Y + o * (BOARD_OPTION_H + 10),
                   BOARD_OPTION_W, BOARD_OPTION_H))
            return o;
    return -1;
}

static BoardResult answer(BoardView *view, CaseFile *file)
{
    if (casefile_answer(file, view->row, view->option)) {
        view->asking = false;
        view->revealed = view->row;
        return BOARD_REVEAL;
    }
    view->wrong_time = 1.6f;
    return BOARD_STAY;
}

BoardResult board_view_update(BoardView *view, CaseFile *file, const InputState *input, float dt)
{
    if (view->wrong_time > 0.0f)
        view->wrong_time = view->wrong_time > dt ? view->wrong_time - dt : 0.0f;
    if (view->asking) {
        if (input->pressed[ACTION_QUIT]) {
            view->asking = false;
            return BOARD_STAY;
        }
        if (input->pressed[ACTION_UP])
            view->option = (view->option + CASE_OPTIONS - 1) % CASE_OPTIONS;
        if (input->pressed[ACTION_DOWN])
            view->option = (view->option + 1) % CASE_OPTIONS;
        int hit = (input->pointer_moved || input->pointer_clicked) ? option_hit(input->pointer_x, input->pointer_y) : -1;
        if (hit >= 0)
            view->option = hit;
        if (input->pressed[ACTION_CONFIRM] || (input->pointer_clicked && hit >= 0))
            return answer(view, file);
        return BOARD_STAY;
    }
    if (input->pressed[ACTION_QUIT])
        return BOARD_BACK;
    int n = casefile_case_clues(view->row, NULL);
    if (input->pressed[ACTION_UP] || input->pressed[ACTION_DOWN]) {
        view->row = (view->row + (input->pressed[ACTION_UP] ? CASE_COUNT - 1 : 1)) % CASE_COUNT;
        int m = casefile_case_clues(view->row, NULL);
        if (view->col >= n) /* On the question: stay on the question */
            view->col = m;
        else if (view->col > m)
            view->col = m;
        n = m;
    }
    if (input->pressed[ACTION_LEFT])
        view->col = (view->col + n) % (n + 1);
    if (input->pressed[ACTION_RIGHT])
        view->col = (view->col + 1) % (n + 1);
    int row, col;
    bool on_slot_click = false, on_card_click = false;
    if ((input->pointer_moved || input->pointer_clicked) && board_hit(input->pointer_x, input->pointer_y, &row, &col)) {
        view->row = row;
        view->col = col;
        on_slot_click = input->pointer_clicked && col == casefile_case_clues(row, NULL);
        on_card_click = input->pointer_clicked && !on_slot_click;
    }
    int clue = board_selected_clue(view);
    if (clue >= 0 && casefile_has(file, clue) && (input->pressed[ACTION_CONFIRM] || on_card_click)) {
        view->examined = clue;
        return BOARD_EXAMINE;
    }
    bool on_slot = view->col == casefile_case_clues(view->row, NULL);
    if (on_slot && (input->pressed[ACTION_CONFIRM] || on_slot_click) && casefile_solved(file, view->row)) {
        view->revealed = view->row; /* Solved: its part of the story again */
        return BOARD_REVEAL;
    }
    if (on_slot && (input->pressed[ACTION_CONFIRM] || on_slot_click) && casefile_ready(file, view->row)) {
        view->asking = true;
        view->option = 0;
        view->wrong_time = 0.0f;
    }
    return BOARD_STAY;
}

/* ---- Story beats ---------------------------------------------------------------- */

/* After the stage that leads into each new landscape: why it changed. */
static const StoryBeat AFTER_STAGE[] = {
    {STORY_PUEBLO,
     {"En dos días, el hospital ya no tenía camas.",
      "A sus muertos los enterraron en el viejo panteón, sin velorio.",
      "Esa misma noche, la tierra empezó a moverse."},
     3, 1},
    {STORY_CEMENTERIO,
     {"Los muertos salieron del panteón y caminaron hacia el pueblo.",
      "La sheriff *Dolores Vega* ordenó el toque de queda.",
      "Una por una, las luces de *Ojo de Cuervo* se apagaron."},
     3, 2},
    {STORY_PUEBLO,
     {"Al amanecer, *Ojo de Cuervo* estaba en silencio.", "Los que seguían en sus calles ya no eran vecinos."},
     2, 3},
    {STORY_NOCHE,
     {"El pueblo cayó, pero el brote no nació aquí.",
      "A unos kilómetros, el *Laboratorio 4* de *Vantrell* sigue encendido.",
      "Y alguien ahí dentro sabe toda la verdad."},
     3, 4},
};

const StoryBeat *story_after_stage(int stage)
{
    /* 1-2 into the graveyard, 1-3 into the night, 1-4 into the ghost town,
     * 1-5 the end of the first route. */
    int k = stage - 1;
    return k >= 0 && k < (int)(sizeof(AFTER_STAGE) / sizeof(AFTER_STAGE[0])) ? &AFTER_STAGE[k] : NULL;
}

void report_open(Report *report, int case_index)
{
    report->case_index = case_index;
    report->time = 0.0f;
}

bool report_update(Report *report, const InputState *input, float dt, bool *stamped)
{
    float before = report->time;
    report->time += dt;
    if (stamped)
        *stamped = before < REPORT_STAMP_AT && report->time >= REPORT_STAMP_AT;
    /* The first moment can't be skipped: the click that answered isn't a close */
    bool close = input->pressed[ACTION_QUIT] || input->pressed[ACTION_CONFIRM] || input->pointer_clicked;
    return !(close && report->time > 0.3f);
}

void exam_open(ClueExam *exam, int clue)
{
    exam->clue = clue;
    exam->time = 0.0f;
}

bool exam_update(ClueExam *exam, const InputState *input, float dt)
{
    exam->time += dt;
    bool close = input->pressed[ACTION_QUIT] || input->pressed[ACTION_CONFIRM] || input->pointer_clicked;
    return !(close && exam->time > 0.2f);
}

/* ---- The tapes ---------------------------------------------------------------- */

const TapeDef TAPES[TAPE_COUNT] = {
    {"LA FILTRACIÓN", -1}, {"EL PANTEÓN", 1}, {"TOQUE DE QUEDA", 2}, {"EL PUEBLO VACÍO", 3}, {"LABORATORIO 4", 4},
};

bool tape_unlocked(const CaseFile *file, int tape)
{
    if (tape < 0 || tape >= TAPE_COUNT)
        return false;
    return TAPES[tape].stage < 0 || (file->beats_seen & (1u << TAPES[tape].stage)) != 0;
}

int tapes_unlocked(const CaseFile *file)
{
    int n = 0;
    for (int t = 0; t < TAPE_COUNT; t++)
        n += tape_unlocked(file, t);
    return n;
}

int tape_view_update(TapeView *view, const CaseFile *file, const InputState *input)
{
    if (input->pressed[ACTION_QUIT])
        return TAPE_BACK;
    if (input->pressed[ACTION_LEFT] || input->pressed[ACTION_UP])
        view->selected = (view->selected + TAPE_COUNT - 1) % TAPE_COUNT;
    if (input->pressed[ACTION_RIGHT] || input->pressed[ACTION_DOWN])
        view->selected = (view->selected + 1) % TAPE_COUNT;
    bool clicked = false;
    if (input->pointer_moved || input->pointer_clicked) {
        for (int t = 0; t < TAPE_COUNT; t++) {
            int x = TAPE_X + t * TAPE_STEP;
            if (inside(input->pointer_x, input->pointer_y, x, TAPE_Y, TAPE_W, TAPE_H + 70)) {
                view->selected = t;
                clicked = input->pointer_clicked;
            }
        }
    }
    if ((input->pressed[ACTION_CONFIRM] || clicked) && tape_unlocked(file, view->selected))
        return view->selected;
    return -1;
}

#define STORY_TYPE_RATE 26.0f /* Letters per second */
#define STORY_LEAD 0.6f       /* Before a line starts typing */
#define STORY_HOLD 2.4f       /* Once typed */
#define STORY_FADE 0.5f

static int letters(const char *s)
{
    int n = 0;
    for (; *s; s++)
        n += ((unsigned char)*s & 0xC0) != 0x80;
    return n;
}

float story_line_length(const char *line)
{
    return STORY_LEAD + (float)letters(line) / STORY_TYPE_RATE + STORY_HOLD + STORY_FADE;
}

void story_start(Story *story, const StoryBeat *beat)
{
    memset(story, 0, sizeof(*story));
    story->beat = *beat;
    story->done = beat->count <= 0;
}

void story_update(Story *story, bool advance, bool skip, float dt)
{
    if (story->done)
        return;
    if (skip) {
        story->done = true;
        return;
    }
    const char *line = story->beat.lines[story->line];
    float typed_at = STORY_LEAD + (float)letters(line) / STORY_TYPE_RATE;
    if (advance)
        story->time = story->time < typed_at ? typed_at : story_line_length(line);
    else
        story->time += dt;
    if (story->time >= story_line_length(line)) {
        story->line++;
        story->time = 0.0f;
        if (story->line >= story->beat.count)
            story->done = true;
    }
}

bool story_caption(const Story *story, char *buf, int size, float *alpha)
{
    if (story->done || size <= 0)
        return false;
    const char *line = story->beat.lines[story->line];
    float t = story->time;
    if (t < STORY_LEAD)
        return false;
    int want = (int)((t - STORY_LEAD) * STORY_TYPE_RATE) + 1, bytes = 0;
    while (line[bytes] && want > 0) {
        bytes++;
        while (((unsigned char)line[bytes] & 0xC0) == 0x80)
            bytes++;
        want--;
    }
    if (bytes >= size)
        bytes = size - 1;
    memcpy(buf, line, (size_t)bytes);
    buf[bytes] = '\0';
    float out = story_line_length(line) - STORY_FADE;
    float a = t > out ? 1.0f - (t - out) / STORY_FADE : 1.0f;
    if (alpha)
        *alpha = a < 0.0f ? 0.0f : a > 1.0f ? 1.0f : a;
    return true;
}
