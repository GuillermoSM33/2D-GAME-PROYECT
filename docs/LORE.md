# Lore de THE MIRACLE

Guion aprobado el 2026-11-11. Aquí está la historia, la intro y el sistema de pistas;
los apartados indican su implementación actual. El juego se llama **THE MIRACLE** (antes Vaquera 2D).

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
`--capturas` guarda un cuadro de cada escena (`0a_intro_*` … `0m_intro_*`). Los sonidos combinan
efectos existentes (pasos, linterna, disparo, vidrio, viento, cuervos, zombis) junto a
grabaciones reales de respiración, zumbido del laboratorio, latido, alarma, estática de radio/cámara
y la sirena. Fuentes y montaje en [AUDIO_CINEMATIC_SOURCES.md](AUDIO_CINEMATIC_SOURCES.md).
El sonido respeta el silencio de la muestra y se corta al saltar la secuencia.

**Cuándo se ve:** la primera vez que se abre el juego, completa. El título entre el polvo se
convierte en la pantalla de título. Las siguientes veces solo sale el título entre el polvo
(unos 4 s) antes del menú. La intro completa se repite desde **Historia** en el título.
Siempre se puede saltar con Enter, Esc o clic.

## Pistas: "Encuentra la causa"

Hecho (2026-11-11). Lógica y textos en `src/game/casefile.c` (pruebas en `tests/test_casefile.c`),
dibujo en `src/game/casefile_render.c`, sprites en `tools/make_clues.py`.

1. **Pistas:** 15, tres por nivel. Una en el **cofre de salida**, otra la lleva **un zombi** de la
   ruta (las dos salen seguro) y la tercera está **escondida en una caja** del camino, para quien
   la rompa. Cada una tiene su propio sprite (`sprites/clues/clues.png`). Al encontrarla, el HUD
   muestra un aviso con su sprite, su nombre y cuántas lleva del nivel. Se guardan en la partida y
   valen para todos los personajes (hay una sola historia).
2. **El Expediente** (título y pausa): un tablero de corcho con un renglón por caso, las pistas
   clavadas y unidas con hilo rojo. Al elegir una pista se lee su texto; si falta, dice en qué
   nivel está y de dónde sale (cofre, zombi o camino).
3. **Deducción:** con todas las pistas de un caso aparece **DEDUCIR**: una pregunta con 3
   respuestas. Equivocarse no castiga. Al acertar se abre el **expediente escrito** del caso: la
   historia extendida y explicada, con su animación corta (la hoja entra y cae el sello de
   RESUELTO). Se puede volver a leer desde el tablero.
4. **El cambio de escenario siempre se explica** al terminar un nivel por primera vez (1-2 a 1-5),
   aunque falten pistas: una escena corta sobre el paisaje del nivel siguiente.

| Caso | Pistas (nivel) | Pregunta |
|---|---|---|
| La paciente cero | Orden de traslado, credencial de prensa, cinta 1 (1-1); registro de ingreso, foto del pasillo, hoja clínica (1-2) | ¿Cómo llegó el brote a Ojo de Cuervo? |
| MRC-2 | Memorándum, informe del día 94, muestra rota (1-3) | ¿Por qué los muertos se levantan? |
| Las cintas | Cintas 2 y 3, tarjeta de acceso (1-4) | ¿Quién ayudaba a Valeria desde dentro? |
| El científico | Bata quemada, plano del prototipo, foto vieja (1-5) | ¿Quién se llevó el prototipo? |

**Examinar:** Enter o clic sobre una pista del tablero la abre a pantalla completa: su dibujo en
grande y una hoja de examen con su tipo, su caso, dónde se halló, su descripción y DETALLES más
finos que dejan cabos sueltos para lo que viene (quién tachó "Laboratorio 4" en la orden, "busquen
a N" en la credencial, la nota "Si cae en malas manos, que sean las mías" en el plano...).

**Texto con énfasis:** en subtítulos, pistas e informes, lo que va entre asteriscos (`*Ojo de
Cuervo*`) sale en otro color: dorado sobre fondo oscuro y rojo tinta sobre papel. Se usa para
nombres, lugares y datos clave; lo que dice Valeria sale en verde agua. Sobre papel el texto va sin
sombra (`pixfont_draw_flat`), que si no se empasta.

## HISTORIA: las cintas

Las animaciones de la historia principal se guardan como **cintas de video** en HISTORIA: *La
filtración* (la intro) y las escenas de fin de nivel (*El panteón*, *Toque de queda*, *El pueblo
vacío*, *Laboratorio 4*), que se desbloquean al verlas. Cada frase de una cinta tiene su propia toma animada
(`src/app/story_render.c`): ataúdes acumulándose en la calle y una tumba que se abre (*El
panteón*); zombis saliendo hacia el pueblo, la sheriff bajo los faroles y los faroles apagándose
(*Toque de queda*); la calle vacía y los "vecinos" quietos (*El pueblo vacío*); las luces del
laboratorio en el horizonte, su pasillo en alarma y alguien frente a los monitores (*Laboratorio 4*). Mientras solo esté la intro, HISTORIA la
reproduce directo. El tablero del Expediente no lleva animaciones de la historia principal: solo
expedientes escritos que la complementan.

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

- Arte que falta: el hospital (para escenas futuras).
