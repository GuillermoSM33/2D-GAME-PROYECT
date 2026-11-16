# Revisión visual de granada y banco

Se revisaron las hojas numeradas a 4×, los detalles de manos a 8× y las
capturas del escenario, con rifle y escopeta y en ambas direcciones.
Cada corrección visual se regeneró y abrió antes de continuar.

| Pregunta de revisión | Observación y corrección |
| --- | --- |
| ¿Se ve natural? ¿Hay movimientos anatómicamente imposibles? | Se retiraron el salto del brazo sobre el casco y los antebrazos duplicados del banco. El lanzamiento usa un balanceo bajo; el cuerpo acompaña el gesto desde la cintura. Los codos sentados quedan a los lados del chaleco y las manos tienen recorridos distintos. |
| ¿Puedo mejorarlo? ¿Cómo? | La primera composición sentada dejaba un codo demasiado abierto y una culata junto a la manga. Se bajó ese codo y se separaron las armas apoyadas del contorno del operador. |
| ¿Hay partes más grandes o fuera de lugar? | El arma del HUD se reemplazó por el equipo de las acciones principales. Casco, chaleco y botas proceden del cuerpo compartido. La granada crecía al soltarla: ahora la mano y el vuelo usan el mismo dibujo. |
| ¿Qué falta para entender la acción? | Se añadieron sacar, preparar, soltar y recuperar en granada; recoger, manipular y apoyar cada arma en banco. Las poses de enlace entre ambas recargas son idénticas y muestran ambas armas. |
| ¿Los objetos están sujetos? | Se abrieron los dedos sobre la parte inferior de la granada, dejando visible su cuerpo. El cargador entra detrás de la boca de la bolsa. Los cartuchos quedan encima de los dedos y se acercan al puerto de carga. |
| ¿La secuencia se lee correctamente dentro del juego? | La revisión del escenario detectó un salto vertical del proyectil: su altura física corresponde al borde inferior, mientras el dibujo en la mano se colocaba por el centro. Se corrigió esa diferencia y el giro empieza en la misma orientación que el objeto sostenido. |

[Granada con ambas armas y direcciones](../../img/swat_granada_juego.gif).
[Banco completo, comenzando con cada arma](../../img/swat_banco_juego.gif).
[Poses del escenario](../../img/swat_aux_poses.png).

Las comprobaciones automáticas complementan esta revisión: cubren todos los
cuadros dibujados y sus reflejos, botas plantadas, enlaces entre armas,
salida única del proyectil, recarga de cada arma una sola vez, sincronía del
sonido y restauración de los tiempos al continuar una partida.

## Corrección del quiebre del brazo al sentarse

La revisión anterior dejó un defecto en los alcances laterales: se alternaban
poses de codo escritas a mano con dos soluciones geométricas distintas. Al
cruzar ciertos puntos de la mano, el codo saltaba y cambiaba el sentido del
pliegue. También había un levantamiento innecesario de la muñeca al sacar el
rifle desde la cadera.

Se sustituyó esa selección por una trayectoria continua. El codo desciende
desde el hombro y abre el alcance hacia el arma; los segmentos proyectados
conservan límites de longitud y el antebrazo mantiene suficiente espacio para
leerse. La manga redondea la unión del codo. La extracción desde la cadera
avanza hacia el apoyo sin subir primero la mano al pecho.

Se abrieron de nuevo las poses ampliadas de ambas armas, los detalles de las
manos y las transiciones de toma, apoyo y recarga. La prueba de regresión
recorre los antiguos puntos de cambio y comprueba que el codo no salte.

[Comparación de los primeros cuadros](../../img/swat_banco_brazos.png).
[Esos cuadros en el escenario, hacia ambos lados](../../img/swat_banco_brazos_juego.png).
