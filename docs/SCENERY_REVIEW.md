# Revisión de decorado e interacción con coches

## Arte

- [Árboles antes/después](images/scenery/trees_before_after.png): las dos variantes tienen ramas conectadas, puntas completas, raíces apoyadas y corteza mate. Revisados también al atardecer, en el cementerio y en ciudad de noche.
- Props nativos: [naturaleza](images/scenery/props_1.png), [mobiliario](images/scenery/props_2.png), [infraestructura](images/scenery/props_3.png). Menos brillo en bordes, sombras de material y plantas con siluetas diferentes; dimensiones y puntos de apoyo conservados.
- [Torre y radar antes/después](images/scenery/equipment_before_after.png): reflector cilíndrico con lente hundida, visera, soporte y cable; plato curvo con costillas, borde enrollado, soportes y pedestal articulado.
- Fachadas [tienda, policía, viviendas y retén](images/scenery/fronts_1.png) y [clínica, taller, subestación y radio](images/scenery/fronts_2.png). Cada fila compara el edificio pintado con el mismo edificio sin pintada. Las dieciséis variantes mantienen la abertura de la puerta.
- [Motos antes/después](images/scenery/motorcycles.png): motor con dos cilindros, aletas, cárter, tubos de bastidor y escape. Se abre el espacio entre piezas y se corrige el recorte de la rueda en las poses inclinadas.
- En el juego: [árboles](images/scenery/trees_game.png), [clínica](images/scenery/clinic_game.png), [radar](images/scenery/radar_game.png).

## Cruce con N

[Sheriff](images/scenery/car_sheriff.gif), [SWAT con rifle](images/scenery/car_swat.gif) y
[SWAT con escopeta](images/scenery/car_swat_shotgun.gif): capturas del juego con entradas
reales, cada una en los dos sentidos (rompiendo el cristal a la derecha, abriendo a la
izquierda).

Secuencia: caminar hasta la manija y tomarla con el brazo casi extendido; abrir, o
levantar el antebrazo, romper el cristal de un puñetazo (las astillas caen y quedan en
la calle) y levantar el botón del seguro por el hueco. Después sube al estribo, se
agacha y entra; sentada en el piso con una rodilla arriba, ya oculta, se empuja hacia
la otra puerta. Empuja la otra puerta, saca una
pierna, asoma la cabeza, se pone de pie y sigue mientras la puerta se cierra. La
camioneta tiene una sola puerta: entra y sale por ella.

Correcciones de esta revisión: antes el coche tapaba al personaje aun estando fuera
(la carrocería se dibujaba encima de todo el cruce) y el cuerpo entero giraba 62° como
una tabla, con el sombrero de lado. Ahora cada cuadro tiene dos capas (fuera y dentro
del coche), el torso se inclina desde la cintura con la cabeza derecha y las piernas
salen de la cadera; dentro va tendida y oculta, así que nada asoma por el techo ni bajo
el piso. Las piernas caminan por distancia, sin deslizarse. El cruce pasó de 5,4 s a
3,5 s (de 6,0 s a 4,3 s rompiendo el cristal).

Segunda revisión: los brazos de la sheriff parecían rotos al pasar por la puerta y la
animación no se entendía. Estaba demasiado cerca de la manija, así que el codo se doblaba
sobre el pecho; tendida dentro era una mancha oscura detrás del poste; al salir
cruzaba los brazos. Ahora se para a un brazo de la manija; cada mano va por ángulo y
alcance desde su hombro, y el codo dobla siempre hacia el mismo lado
(`test_car_arms_never_fold_up`). El golpe al cristal es un puño levantado que baja, no
un brazo cruzado sobre el pecho. El vidrio del frontal es semitransparente: se la ve
cruzar. La puerta abierta deja un hueco más ancho.

Tercera revisión (romper la ventana): al quitar el seguro el antebrazo se escondía tras
la puerta y quedaba un muñón con la mano flotando; en la hoja había pedazos de brazo y
pierna sueltos, y dentro del coche la cabeza se hundía en los hombros. Ahora la mano se
queda en el hueco de la ventana con el brazo entero, se ve el botón del seguro subir, las
astillas aterrizan donde el juego deja el vidrio en la calle (y no antes), cada cuadro
está completo en una sola fila y dentro va sentada en el piso con una rodilla arriba.

Cuarta revisión: se veía estirada y con brazos antinaturales (sus brazos medían 16.5 px y
en todas sus demás hojas miden 13), el auto se veía chico, su sombrero se veía por la
ventana estando dentro y los camiones militares parecían de su tamaño. Ahora usa sus
brazos reales, los autos son 1.2 veces más grandes y los camiones 1.6, dibujados nativos
a esa escala, y el vidrio la tapa al estar dentro.

Puertas bloqueadas y alarmas operativas se determinan por coche. El cristal roto y
la activación quedan guardados; repetir N no vuelve a decidir la alarma. Estos estados
son independientes de los impactos que dañan y hacen explotar el vehículo. Un obstáculo
al otro lado impide iniciar el cruce. Se puede guardar y continuar la animación.

## Comprobación

### Tren laboratorio y escala de la calle

Las fachadas ahora miden 288 × 200 (oeste) y 288 × 216 (ciudad), con la abertura
de 44 × 64 conservada. El cálculo de separación de casas incluye la anchura
visual completa y el paralaje, también después de destruir una puerta.

[Revisión del tren en el juego](images/scenery/train_lab_game.png): acceso desde
el patio, prototipos, criogenia, una pieza en su cuna, la escotilla cerrada y la
locomotora al salir. Son trece vagones numerados, más maquinaria y control. E
permite entrar, recoger las piezas, consultar el Archivo 4 y salir. Los treinta
infectados están distribuidos en quince parejas. La terminal dirige la historia a
Cerro Gris, búnker 2.

Correcciones de esta revisión: la locomotora ya no se reescala (se veía cortada
y deformada) y ahora es una unidad de maquinaria y una de control dibujadas a
píxel nativo; dentro, la cámara no pasa de las paredes finales, así que no
aparece vacío en el vagón 01 ni en control; el interior dejó los colores planos
por materiales, luz de tubos y desgaste; las piezas miden 32 × 32, tienen
silueta propia, halo, columna de luz y marcador, y descansan en cunas dibujadas
en la sala. La tarjeta del tren (vagón, mapa y objetivos) vive bajo la franja
del HUD, sin encimarse con suministros ni estados, y el aviso de pieza va en la
columna derecha. La cinta 8 (al terminar 2-3) dibujaba encima del tren la puerta
del muro de dos vagones de antes; con el tren laboratorio quedaba flotando entre los
vagones 05 y 06. Ya no se dibuja.

`test_train` recorre las quince habitaciones con el movimiento real del jugador,
comprueba que la entrada y la salida no se pueden omitir, verifica las ocho
piezas entre 2-3, 2-4 y 2-5 y termina la misión después de salir. También
comprueba que los avisos dicen qué falta y solo ofrecen E cuando actúa, que la
cámara no sale del tren, el orden del objetivo siguiente y el conteo por vagón. Las pruebas de
persistencia reanudan dentro del vagón 7 y conservan piezas al abandonar;
también leen los esquemas antiguos de guardado. Las hojas del laboratorio y
los módulos se regeneran exactamente desde `train_art.py`, y sus puntos de
interacción coinciden con las constantes `TRAIN_*_ART` del juego.

`tests/test_scenery_assets.py` comprueba regeneración exacta, geometría de hojas,
alfa de luces, conectividad de los árboles, parejas pintadas/sin pintar y celdas sin
recortes. Las pruebas C cubren cruces en ambos sentidos, puertas libres/bloqueadas,
alarma/silencio, límites, resistencia independiente, guardado y compatibilidad con
partidas anteriores. La revisión visual se realiza además de esas pruebas.
