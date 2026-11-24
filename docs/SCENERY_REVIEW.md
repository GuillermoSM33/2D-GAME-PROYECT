# Revisión de escenarios, tren y personajes

## Arte de los escenarios

- [Árboles antes/después](images/scenery/trees_before_after.png): ramas conectadas, puntas completas, raíces apoyadas y corteza mate. Revisados también al atardecer, en el cementerio y en ciudad de noche.
- Props nativos: [naturaleza](images/scenery/props_1.png), [mobiliario](images/scenery/props_2.png), [infraestructura](images/scenery/props_3.png). Menos brillo en bordes, sombras de material y plantas con siluetas diferentes; dimensiones y puntos de apoyo conservados.
- [Torre y radar antes/después](images/scenery/equipment_before_after.png): reflector con lente hundida, visera, soporte y cable; plato curvo con costillas, borde enrollado, soportes y pedestal articulado.
- Fachadas de [tienda, policía, viviendas y retén](images/scenery/fronts_1.png) y de [clínica, taller, subestación y radio](images/scenery/fronts_2.png). Cada fila compara el edificio pintado con el mismo edificio sin pintada. Las dieciséis variantes mantienen la abertura de la puerta.
- [Motos antes/después](images/scenery/motorcycles.png): dos cilindros, aletas, cárter, tubos de bastidor y escape, con espacio entre piezas y ruedas completas en las poses inclinadas.
- En el juego: [árboles](images/scenery/trees_game.png), [clínica](images/scenery/clinic_game.png) y [radar](images/scenery/radar_game.png).

Las fachadas miden 288 × 200 en el oeste y 288 × 216 en ciudad, con la abertura de
44 × 64 conservada. La separación de edificios incluye su anchura visual y el
paralaje. El reparto de objetos de la calle tiene en cuenta la huella real de
vehículos, obstáculos e interactuables para evitar que la decoración se monte
sobre ellos.

## Tren laboratorio

Son **quince salas**: trece vagones numerados, la unidad de maquinaria y la
locomotora de control. Los **treinta infectados** se distribuyen en quince parejas.
E permite entrar desde el patio, recoger tableta y piezas, ponerse o quitarse el
traje, consultar el Archivo 4 y salir. La terminal conserva el destino de la
historia: Cerro Gris, búnker 2.

[Acceso al tren desde el patio](images/scenery/train_00_entry.png).

El tren conserva su tamaño grande; el mobiliario usa como referencia a los
personajes de unos 64 píxeles de altura. El refrigerador mide 68 píxeles, los
mostradores unos 36 y las sillas unos 34; mesas, herramientas, rifles y utensilios
mantienen la misma escala humana. Cada pieza se dibuja en sus dimensiones
nativas, sin reducir imágenes terminadas.

Las salas contienen carritos, gabinetes, bandejas, suministros pequeños, papeleras,
bitácoras, avisos y objetos de la tripulación. Tuberías sujetas a la pared,
canaletas, cuadros eléctricos y cinco extractores animados ocupan el espacio alto
del vagón. En Cirugía y Enfermería, las cortinas quedan unidas al techo mediante
placas, varillas, rieles y anillas; llegan cerca del piso y su abertura deja ver la
camilla que protegen.

Las siete cajas del interior tienen bahías propias, separadas de los muebles y de
las cunas de piezas. `TRAIN_SUPPLY_BAYS` comparte sus posiciones entre el código C
y el generador de arte; también reserva espacio para la caja de la pista del
contenedor. Los marcos de los extractores y sus aspas usan las coordenadas
compartidas de `TRAIN_VENT_FANS`.

| Sala | Captura real |
| --- | --- |
| Comedor: refrigerador, mostrador, mesa y caja separados | [Vagón 10](images/scenery/train_10_interior.png) |
| Enfermería: camas, cortina soportada y equipo médico | [Vagón 11](images/scenery/train_11_interior.png) |
| Armería: rifles, chalecos, cajas y banco de limpieza | [Vagón 12](images/scenery/train_12_interior.png) |

[Composición de las tres salas](images/scenery/train_rooms_review.png).

### Tableta e inventario

El escenario queda despejado de la tarjeta persistente de objetivos. **E recoge
la tableta del vagón 01 y abre su mapa y briefing una vez.** M permite volver a
abrirlo o cerrarlo; P abre el inventario y cambia entre ambas consultas. Esc o
Enter cierran la consulta. Mientras está abierta, la simulación permanece
pausada: no avanzan jugadores, infectados, proyectiles, fusibles ni el reloj de
misión. El mapa requiere haber recogido la tableta; el inventario está disponible
antes de encontrarla.

La tableta tiene marco, pantalla y planos de pixel art propios. Presenta los
quince vagones, posición actual, infectados pendientes, gases, trajes, piezas,
terminal y la lista de objetivos con su destino y estado. El inventario es un
estuche de metal azul petróleo con forro marino y herrajes de cobre; muestra
retrato, equipo, armas, munición, agua, dinamita, oro y módulos recuperados.
Cada fila se enfoca con W/S, flechas, rueda o ratón; un panel explica el objeto
y Enter/E o el botón ejecutan su acción: equipar o recargar, beber, colocar
dinamita, abrir el mapa o el expediente. Los tres recursos de interfaz se
generan con `tools/make_field_ui.py`.

- [Mapa y objetivos dentro de la tableta](images/scenery/train_01c_map.png).
- [Inventario de la sheriff](images/scenery/train_03d_inventory_0.png) y [del SWAT](images/scenery/train_03d_inventory_1.png), ambos con el traje puesto.
- [Composición de mapa, inventarios y acceso](images/scenery/train_ui_review.png).

Durante la partida solo aparece brevemente el aviso de pieza recién recuperada,
separado del HUD. Los avisos de interacción ofrecen E cuando actúa y explican qué
falta ante una terminal o salida bloqueada. Pulsar E en esos puntos no planta
dinamita por accidente.

### Trajes aislantes

[Revisión de las animaciones de ambos trajes](images/hazmat_review.png).

La sheriff corre con el traje sobre sus mismas articulaciones
([cuadros](images/hazmat_legs_review.png), [animación](images/hazmat_walk_review.gif)).
El traje se compone con las capas de brazos y armas de sus propias hojas: la mochila
está en todos los cuadros y no quedan paños, cortes ni huecos junto a los brazos.

La sheriff lleva capucha redonda, visor azul y un overol amarillo holgado de
silueta neutra: oculta cabello, sombrero, corsé y cintura ajustada. El SWAT lleva
visor naranja y protección adicional claramente visible sobre el traje: chaleco
de placas, collarín, hombreras, refuerzos en brazos y rodillas, guantes y botella
de aire. Las armas mantienen su dibujo y sus colores.

Los trajes se aplican a todas las animaciones, incluidas recarga, salto, asiento,
caída, linterna y cruce de vehículos. Las hojas de `characters/<id>/suit/` se
regeneran con `tools/make_hazmat.py`; no se retocan de forma aislada. El traje
protege del aire tóxico de Cultivos (03) y Criogenia (07), y se deja al salir del
tren.

### Vehículos de las cinemáticas

[Convoy y ruedas en movimiento](images/scenery/convoy_wheels.gif).

Los camiones usan una sola rueda por eje, colocada sobre la rueda de su propio
sprite y animada según el desplazamiento del vehículo. Se elimina así el juego
de ruedas añadido a distinta altura sobre la carrocería. Los bogies ferroviarios
tienen ruedas de radio 16, mayor separación entre ejes y su bastidor conectado al
vagón. Locomotora y maquinaria se dibujan a tamaño nativo; la cinta 8 conserva el
tren completo sin la antigua puerta que quedaba flotando entre vagones.

## Cruce de coches con N

[Sheriff](images/scenery/car_sheriff.gif), [SWAT con rifle](images/scenery/car_swat.gif)
y [SWAT con escopeta](images/scenery/car_swat_shotgun.gif): capturas del juego con
entradas reales en ambos sentidos, rompiendo el cristal o abriendo la puerta.

El personaje camina hasta la manija y la toma a un brazo de distancia. Abre o
rompe el cristal con el puño, quita el seguro y pasa por el habitáculo; sale por
la otra puerta y continúa mientras esta se cierra. La camioneta de una puerta
entra y sale por esa misma puerta. Las astillas caen donde quedan en la calle.

Cada cuadro conserva el cuerpo completo en una de las dos capas del cruce:
fuera o dentro. El torso se inclina desde la cintura, la cabeza se mantiene
derecha y los brazos conservan la longitud de las demás animaciones. Dentro va
sentada en el piso, con una rodilla levantada; carrocería y vidrio ocultan el
cuerpo, salvo por una puerta abierta. Ninguna parte sale por el techo o bajo el
piso. Los coches se dibujan nativos a escala 1.2 y los camiones militares a 1.6.

[Continuidad de la camioneta azul](images/scenery/blue_wagon_continuity.png):
conserva techo largo, ventana de carga y montantes al estar entera, dañada o
quemada. Las capas de carrocería y frontal mantienen ese mismo modelo con
cristales enteros o rotos y con ambas puertas en sus distintos estados. Abrir una
puerta no transforma la camioneta en un sedán.

Puertas bloqueadas y alarmas se determinan por coche. Cristal roto, activación de
alarma y daño de carrocería mantienen estados independientes y quedan guardados.
Un obstáculo al otro lado impide iniciar el cruce; se puede guardar y continuar
la animación.

## Recarga de las duales al caminar

[Antes/después en movimiento](images/scenery/dual_reload_walk_before_after.gif).

La recarga conserva manos, brazos y revólveres completos mientras las piernas
caminan. El corte del torso tiene en cuenta los puntos de apoyo de ambas hojas;
una capa de acción continúa debajo de la cintura para que ni la mano ni el arma
se recorten junto a las piernas. Se comprueba en ambas manos, sentidos y fases
del paso. La corrección conserva el gesto de recarga a la altura del cinturón y
los contadores independientes de los dos tambores.

## Comprobaciones

- `tools/make_field_ui.py --verify`: las tres hojas propias de tableta, estuche y planos se regeneran exactamente; el ejecutable valida tamaños y distribución de texto.
- `tests/test_hazmat.py` y `tools/make_hazmat.py --verify`: silueta neutra, visores y protecciones correctos, armas y manos conservadas en todas las variantes, piernas que no se cruzan al caminar y ningún contorno suelto; 76 hojas reproducibles.
- `tests/test_scenery_assets.py`: regeneración exacta, hojas completas, escala humana, siete bahías de cajas libres, soporte y longitud de cortinas, marcos de extractores y posiciones de interacción compartidas con el juego.
- `tests/test_train.c`: recorrido de las quince salas con movimiento real, entrada y salida obligatorias, ocho piezas entre 2-3, 2-4 y 2-5, tableta y traje, gases, objetivos, conteo de tripulación y cajas en sus bahías.
- `tests/stage_audio.c`: tomar la tableta con E abre el briefing; M/P/Esc/Enter cambian y cierran las consultas sin avanzar el mundo; se conservan las restricciones de E y los puntos bloqueados no consumen dinamita.
- `tests/player_render.c`: píxeles reales de las recargas, capas sobre las piernas, ambos sentidos y continuidad al cruzar coches.
- `tests/car_model_art.py`: identidad de sedán, camioneta abierta y camioneta azul a través del daño, cristales y capas de puertas; comparación con los PNG instalados.
- `tests/cinematic_render.c`: posición de ejes y animación de ruedas de los vehículos de las cinemáticas.
- Pruebas de persistencia: reanudación dentro del vagón 7, conservación de piezas y compatibilidad con esquemas anteriores.

Las capturas PNG de esta revisión proceden del ejecutable; las composiciones
reúnen capturas completas a su resolución original. La revisión visual acompaña
a las pruebas de lógica, renderizado y regeneración.
