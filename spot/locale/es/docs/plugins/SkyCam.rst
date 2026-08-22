++++++++
Sky Cams
++++++++

El complemento SkyCam se usa para colocar una imagen de cámara de todo el
cielo en el fondo del canal Targets, como ayuda para vigilar las condiciones
del cielo. Hay un menú desplegable con varios sitios entre los que elegir.

Establecer la imagen del cielo
==============================

Seleccione el servidor de cámara que desee usar en el menú desplegable bajo
"All Sky Camera". Luego marque la casilla junto a "Show Sky Image" para
mostrar la imagen en la ventana `<wsname>_TGTS`. Puede tardar unos momentos
en aparecer la imagen del cielo. Cuando la imagen se actualice, la hora y la
fecha de la última imagen se mostrarán en la parte inferior de la ventana,
debajo de "Image Download Info".

El complemento SkyCam también puede generar una imagen diferencial a partir
del servidor de canal seleccionado marcando la casilla junto a "Show
Differential Image".

Añadir cámaras nuevas
=====================

Puede añadir con facilidad sus propias imágenes de cámara de todo el cielo si
dispone de un flujo adecuado de imágenes que puedan obtenerse mediante
protocolos web. Si tiene descargado el código fuente de SPOT, encontrará el
archivo "skycams.yml" en .../spot/spot/config/. Copie este archivo a
$HOME/.spot y edítelo para añadir su propia cámara. Deberá proporcionar una
URL para descargar imágenes, un título, un píxel central (coordenadas X e Y)
en la imagen que represente el cenit, el radio del círculo hasta el horizonte
en píxeles, una rotación que aplicar, si se debe voltear la imagen en las
dimensiones X o Y, y un intervalo de actualización medido en segundos.

Reinicie spot y debería poder elegir su nueva cámara en la lista.
