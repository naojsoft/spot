SiteSelector
============
El complemento SiteSelector se usa para seleccionar el lugar desde el que
piensa observar, así como la hora de observación en ese lugar.

Casi siempre querrá iniciar este complemento primero, porque controla muchos
de los aspectos de los otros complementos visibles en el espacio de trabajo.

Establecer el lugar de observación
----------------------------------
Use el menú desplegable "Site:" para seleccionar el lugar de observación. Hay
varios sitios predefinidos disponibles.

Añadir su propio lugar de observación personalizado
---------------------------------------------------
Si el lugar que desea no está disponible, puede añadir el suyo con
facilidad. Si tiene descargado el código fuente de SPOT, encontrará el
archivo "sites.yml" en .../spot/spot/config/. Copie este archivo a
$HOME/.spot y edítelo para añadir su propio sitio. Asegúrese de establecer
todas las claves de su sitio (latitud, longitud, elevación, etc.). Reinicie
spot y debería poder ver su nuevo lugar.

Establecer la hora de observación
---------------------------------
La hora puede fijarse a la hora actual o a una hora fija. Para fijarla a la
hora actual, elija "Now" en el menú desplegable "Time mode:".

Para fijar una hora fija, elija "Fixed": esto habilitará los controles "Date
time:" y "UTC offset (min):". Introduzca la fecha/hora en el primer cuadro
con el formato YYYY-MM-DD HH:MM:SS y pulse "Set".

De forma predeterminada, el desfase UTC de la hora fija se establecerá al de
la zona horaria del lugar de observación; pero puede introducir un desfase
personalizado (en *minutos*) respecto a UTC en el otro cuadro y pulsar "Set"
para indicar un desfase especial con el que interpretar la hora.

.. note:: esto NO cambia la zona horaria del lugar de observación; solo fija
          la interpretación de la hora fija que está estableciendo.

Actualización de los complementos
---------------------------------
Siempre que cambie el lugar de observación o la hora, los demás complementos
deberían actualizarse automáticamente (si se suscriben a los cambios de sitio
y hora, como están diseñados la mayoría).

.. important:: Cerrar este complemento puede hacer que otros no funcionen
               como se espera. SiteSelector es importante como fuente de las
               actualizaciones de tiempo para casi todos los demás
               complementos, y si lo cierra por completo, su rastreador de
               tiempo dejará de activar las actualizaciones en esos otros
               complementos. En caso de duda, inicie y minimice este
               complemento en lugar de cerrarlo.
