++++++++
Sky Cams
++++++++

El complemento SkyCam se usa para colocar una imagen de cámara de todo el
cielo en el fondo del canal Targets, como ayuda para vigilar las condiciones
del cielo. Hay un menú desplegable con varios sitios entre los que elegir.

Establecer la imagen del cielo
==============================

Seleccione el servidor de cámara que desee usar en el menú desplegable bajo
"Cámara de todo el cielo". Después, marque la casilla junto a "Mostrar imagen del cielo" para
mostrar la imagen en la ventana `<wsname>_TGTS`. La imagen del cielo puede
tardar unos instantes en aparecer. Cuando la imagen se actualiza, la fecha y
la hora de la última imagen se muestran en la parte inferior de la ventana,
bajo "Información de descarga de imagen".

Algunas cámaras de todo el cielo producen imágenes en color. Al marcar la
casilla "Monocromo" se convierten en una imagen monocroma (escala de
grises); desmárquela para ver los colores originales.

La imagen del cielo se dibuja con el mapa de colores y los niveles de corte
del visor, de modo que puede ajustar su contraste y sus niveles de corte con
los controles habituales del visor (en una imagen en color solo se aplican
los niveles de corte). Sus ajustes se conservan cuando llegan imágenes
nuevas.

Imagen diferencial
==================

Marque la casilla junto a "Mostrar imagen diferencial" para mostrar cómo ha
cambiado el cielo entre las dos últimas imágenes de la cámara, en lugar de
la propia imagen. Así es mucho más fácil ver las nubes que se mueven o se
forman. Con el mapa de colores predeterminado "Gris", las zonas que no han
cambiado aparecen en gris medio, las que se han vuelto más brillantes, más
claras, y las que se han oscurecido, más oscuras. Las nubes iluminadas por
la Luna o por las luces de las ciudades suelen volverse más brillantes; las
nubes que ocultan las estrellas o la Vía Láctea se oscurecen.

Para crear la imagen diferencial, ambas imágenes se convierten a monocromo,
se reduce su resolución y se les aplica un filtro de mediana, lo que elimina
la mayoría de las estrellas y del ruido. La imagen anterior se escala para
igualar el brillo general de la actual, de modo que los cambios en la
exposición de la cámara no parezcan nubes. A continuación, la diferencia se
divide por una estimación del ruido de la imagen, así que la imagen
diferencial está en unidades del ruido ("sigma").

Los controles son:

* "Compensar rotación del cielo": el cielo gira aproximadamente un cuarto de grado por
  minuto, por lo que las estrellas se mueven entre imágenes. Con esta opción
  marcada, la imagen anterior se gira alrededor del polo celeste hasta la
  hora de la imagen actual, de modo que las estrellas se anulan y solo
  quedan los cambios reales. Para ello, la orientación de la cámara en
  skycams.yml debe ser correcta (véase "Añadir cámaras nuevas"). Los objetos
  fijos en el campo de la cámara, como cúpulas o árboles cerca del
  horizonte, pueden dejar entonces trazos curvos.

* "Umbral": un cambio mayor que este número de sigmas cuenta como nube
  para la nubosidad (valor predeterminado 5).

* "Mapa de colores": el mapa de colores de la imagen diferencial. "Gris" y
  "Cambio" (que muestra solo la magnitud del cambio, no si la zona se volvió
  más brillante o más oscura) mantienen legibles las superposiciones de los
  objetivos; "Turquesa/Ámbar" y "Azul/Rojo" muestran el sentido del cambio en
  color.

* "Nubosidad": el porcentaje del cielo a menos de 75 grados del cenit que
  ha cambiado más que el umbral. Mide las nubes que se mueven o cambian
  entre imágenes; un cielo cubierto uniforme que no cambia no aparecerá.
  Mientras el Sol está a menos de 12 grados por debajo del horizonte en la
  cámara, el brillo del cielo cambia demasiado deprisa para que el valor
  tenga sentido, así que se muestra "Crepúsculo" o "Sol arriba" en su
  lugar.

La imagen diferencial mantiene su propio mapa de colores y sus propios
niveles de corte (de -10 a +10 sigma por defecto), separados de los de la
imagen normal, y también puede ajustarlos con los controles habituales del
visor.

Tras seleccionar una cámara, la imagen diferencial aparece cuando se ha
recibido una segunda imagen. Si una descarga devuelve la misma imagen que la
anterior (la cámara aún no se ha actualizado), se ignora.

El botón "Guardar configuración" guarda sus selecciones actuales (servidor de cámara,
"Mostrar imagen del cielo", "Mostrar imagen diferencial" y "Monocromo") para el espacio
de trabajo, de modo que se restauren la próxima vez que se abra.

Añadir cámaras nuevas
=====================

Puede añadir fácilmente sus propias imágenes de cámaras de todo el cielo si
dispone de una fuente de imágenes adecuada que pueda obtenerse mediante
protocolos web. Si tiene descargado el código fuente de SPOT, encontrará el
archivo "skycams.yml" en .../spot/spot/config/. Copie este archivo a
$HOME/.spot y edítelo para añadir su propia cámara. Deberá indicar una URL
para descargar las imágenes, un título, un píxel central (coordenadas X e Y)
de la imagen que represente el cenit, el radio en píxeles del círculo hasta
el horizonte, una rotación que aplicar, si se debe voltear la imagen en las
dimensiones X o Y, y un intervalo de actualización medido en segundos.
También puede indicar la ubicación de la cámara en grados como "latitude"
(negativa en el hemisferio sur) y "longitude" (negativa al oeste de
Greenwich). La latitud se usa para compensar la rotación del cielo en la
imagen diferencial, y ambas se usan para saber cuándo es de noche en la
cámara. Si no se indican, se usa la ubicación del sitio seleccionado en
SPOT, lo cual es incorrecto si la cámara está en otro sitio.

Algunas cámaras solo publican una imagen animada (por ejemplo, un bucle GIF
de las últimas imágenes). En ese caso SPOT usa el último fotograma de la
animación, que normalmente es el más reciente; para usar otro fotograma,
indique su número como "frame" (contando desde 0, o desde -1 para el
último).

La rotación y los volteos deben orientar la imagen de modo que el norte
quede arriba y el este a la izquierda, como en el gráfico polar del cielo
(en ambos hemisferios). Una buena comprobación es que la Luna o un planeta
brillante de la imagen del cielo coincida con su posición en SPOT, y que las
estrellas se anulen en la imagen diferencial con "Compensar rotación del cielo" marcado.

Reinicie spot y debería poder elegir su nueva cámara en la lista.
