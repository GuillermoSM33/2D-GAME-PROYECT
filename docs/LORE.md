# Lore de THE MIRACLE

Guion aprobado el 2026-11-11. Todavía no hay nada de esto en el código: aquí está la historia,
la intro y el sistema de pistas, para construirlos. El juego se llama **THE MIRACLE** (antes Vaquera 2D).

**Regla:** la historia se cuenta **por fases**. La intro solo engancha y deja preguntas; las
respuestas llegan conforme el jugador avanza y junta pistas. No adelantes en la intro nada que
le toque a una fase posterior.

**Sin voces:** la historia se cuenta solo con cinemáticas, ruidos y texto en pantalla. No hay
doblaje ni narración hablada; los diálogos van escritos.

Todos los nombres de compañías y pueblos son **inventados**; no uses nombres reales de
compañías ni de pueblos.

## Dónde pasa

**Ojo de Cuervo**, un pueblo del desierto en la frontera entre Estados Unidos y México. Sus
nombres mezclan inglés y español, igual que sus personajes. Cerca, en el desierto, está el
**Laboratorio 4** de Vantrell.

## Personajes

| Quién | Nombre | Papel |
|---|---|---|
| Sheriff (`cowgirl`) | **Dolores "Lola" Vega** | La sheriff de Ojo de Cuervo. Conserva la estética de la vaquera y sus armas; lleva **placa** |
| SWAT (`swat`) | **Sargento Tomás Reyes** | Del pelotón que el gobierno asignó como escolta personal del director Vantrell |
| Tercer personaje (`hero`, "Prototipo") | **Dr. Elías Navarro** | El científico de Vantrell que filtró todo. Sacó del laboratorio el cañón de plasma experimental. Su identidad se revela en una fase |
| La reportera | **Valeria Ortiz** | Amiga de Navarro. Grababa dentro del laboratorio; es la paciente cero |
| El director | **Julian Vantrell** | Hijo del fundador y director de la farmacéutica |
| La compañía | **Vantrell Pharmaceuticals** | Desarrolló The Miracle con ayuda del gobierno |

## The Miracle (el patógeno)

"The Miracle" es el nombre comercial del proyecto: una bacteria diseñada con IA para blindar el
cuerpo contra cualquier enfermedad (influenza, covid…). Por dentro, el laboratorio usa nombres de
cepa, y esos nombres aparecen en las pistas antes de que el jugador los entienda:

- **MRC-1:** una mala mezcla de ADN creó un patógeno muy contagioso, con mutación pasiva. Se
  extendía por todo el cuerpo y su blindaje impedía revertir su evolución.
- **MRC-2:** reorganizaron su ADN combinándolo con patógenos más frágiles. Pareció resolverse;
  tiempo después se reactivó y mutaba al doble de velocidad. Eso altera el metabolismo y provoca
  una falla sistémica de los órganos, pero la mutación obliga al cuerpo a mantener funciones
  mínimas: muerte clínica seguida de una aparente reanimación.

En la intro solo se dice "patógeno" o "The Miracle". La gente del pueblo puede llamarlo "virus"
por error; la diferencia se aclara en la fase de la ciencia.

## La fuga (lo que pasó, completo)

Cuando marcaron el patógeno como inestable, contrataron mercenarios para borrar todo rastro del
laboratorio: no querían que se ligara al gobierno con algo tan peligroso. Navarro, al ver los
resultados, contactó a Valeria Ortiz para sacar la verdad y que cancelaran el proyecto. Mientras
ella grababa, un mercenario la descubrió. Valeria tomó una muestra como escudo para que no le
dispararan; el mercenario disparó de todos modos, rompió el contenedor y el patógeno entró por la
herida de bala. La llevaron al hospital de Ojo de Cuervo, contagió a los médicos y de ahí se
extendió por el pueblo.

## Intro: "La filtración" (unos 75 s)

| # | Lo que se ve | Texto | Sonido |
|---|---|---|---|
| 1 | Negro. Se enciende la imagen de una cámara (REC, la hora): *VANTRELL — Laboratorio 4*. Un pasillo de noche | — | Respiración, pasos bajos |
| 2 | Vitrinas y monitores con ADN | *"Lo llamaron The Miracle. Una cura para todas las enfermedades."* | Zumbido de máquinas |
| 3 | Un monitor en rojo; la bacteria se divide y cambia de forma | *"Lo que crearon no se podía detener."* | Latido |
| 4 | Linternas al fondo del pasillo: los mercenarios | *"Alguien vino a borrar todo rastro."* | Radio con estática |
| 5 | En primera persona: el primer mercenario de frente, rifle y linterna a la cámara, el segundo detrás; Valeria levanta la muestra | *"¡Si disparas, se rompe!"* | Silencio |
| 6 | **Dispara:** fogonazo, sacudida, la cámara cae al piso, estática y queda **NO SIGNAL** | — | Disparo, vidrio, golpe metálico |
| 7 | Carretera del desierto al amanecer; una ambulancia | *"La llevaron al hospital de Ojo de Cuervo."* | Sirena que se aleja |
| 8 | El pueblo al atardecer, cada vez más vacío | *"En tres días, el pueblo dejó de contestar."* | Viento, cuervos |
| 9 | El cementerio de noche: zombis salen de dos tumbas abiertas y de un ataúd que revienta | *"Los muertos no se quedaron quietos."* | Tierra, madera, gruñidos |
| 10 | La sheriff Vega mira el pueblo y camina hacia él; el título **THE MIRACLE** y el lema *La cura era la plaga* salen del polvo, que sigue soplando en el menú | — | Entra `menu.ogg` |

El disparo se cuenta desde la cámara, sin mostrar la herida. Las escenas 1 a 6 se ven desde
la cámara de Valeria: el laboratorio va a oscuras, con linternas y siluetas.

**Estado (2026-11-11):** hecha y jugable. Lógica y guion en `src/game/intro.c` (con pruebas en
`tests/test_intro.c`), dibujo en `src/app/intro_render.c`, arte en `tools/make_cinematics.py`.
`--capturas` guarda un cuadro de cada escena (`0a_intro_*` … `0m_intro_*`). Los sonidos usan por
ahora efectos que ya existían (pasos, linterna, disparo, vidrio, viento, cuervos, zombis); faltan
grabaciones propias para el zumbido del laboratorio, el latido, la alarma, la estática de radio y
la sirena.

**Cuándo se ve:** la primera vez que se abre el juego, completa. El título entre el polvo se
convierte en la pantalla de título. Las siguientes veces solo sale el título entre el polvo
(unos 4 s) antes del menú. La intro completa se repite desde **Historia** en el título.
Siempre se puede saltar con Enter, Esc o clic.

## Pistas: "Encuentra la causa"

1. **Pistas:** unas 3 por nivel, en los cofres de salida y escondidas en las misiones. Tipos:
   cintas de Valeria 📼, documentos de Vantrell 📄, fotos y objetos del pueblo 📷 y muestras 🧪.
   Cada una tiene su propio sprite. Al recogerla, el HUD muestra su sprite y el conteo del nivel.
2. **El Expediente:** un tablero de corcho con las pistas clavadas y unidas con hilo rojo. Se
   abre desde la pausa y desde el Almanaque.
3. **Deducción:** cuando una parte del tablero está completa, aparece una pregunta con 3
   respuestas. Al acertar se abre la minicinemática de esa fase. Equivocarse no castiga: se
   vuelve a intentar.
4. **El cambio de escenario siempre se explica** al final del nivel, aunque falten pistas. Las
   pistas dan el porqué de fondo; quien no investiga entiende la historia igual.

## Fases de la ruta 1

| Al terminar | Escena corta (siempre) | Lo que revelan las pistas completas |
|---|---|---|
| 1-2 → cementerio | El hospital se saturó y empezaron a enterrar a los muertos | Registro del hospital: la paciente cero llegó con un disparo, no enferma |
| 1-3 → noche | Los muertos del cementerio se levantan; la sheriff ordena el toque de queda | La ciencia: MRC-1 → MRC-2 y por qué los cuerpos "reviven" |
| 1-4 → pueblo fantasma | El pueblo se vació en una noche | Cintas de Valeria: alguien le pasaba información desde Vantrell |
| 1-5 | Cierre de la ruta 1 | El científico: Navarro y lo que se llevó del laboratorio |

Para rutas futuras: los mercenarios y la conexión con el gobierno, dónde estaba Reyes la noche
de la fuga y qué pasó con Valeria.

## Pendiente

- La vaquera pasa a sheriff: nombre en la elección de personaje y la placa en las tablas de
  `tools/rework_cowgirl.py` (nunca en una sola hoja).
- Arte nuevo que falta: hospital, tablero del Expediente y sprites de pistas.
- Sonidos propios de la intro (zumbido, latido, alarma, estática, sirena), con fuente CC0 como
  pide `docs/AUDIO.md`.
