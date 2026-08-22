++++++++++++++
Instrument FOV
++++++++++++++

El complemento Instrument FOV se usa para superponer el campo de visión de un
instrumento sobre una imagen de sondeo en la ventana `<wsname>_FIND`.

.. note:: Es importante haber descargado previamente en el visor de búsqueda
          (con el complemento "FindImage") una imagen con un WCS preciso para
          que este complemento funcione correctamente.

Seleccionar el instrumento
==========================

El instrumento puede seleccionarse pulsando el botón "Choose" bajo
"Instrument" y luego navegando por el menú hasta encontrar el instrumento
deseado. Una vez seleccionado el instrumento, el nombre se rellenará en
"Instrument:" y aparecerá un contorno del campo de visión del instrumento en
la ventana `<wsname>_FIND`.

El ángulo de posición puede ajustarse, lo que ajustará el ángulo de la
superposición del FOV del instrumento sobre la imagen. Si la casilla "Rotate
w/PA" está marcada, la imagen del visor se rotará para que la superposición
del FOV mantenga la misma orientación.

La RA y la DEC se rellenarán automáticamente al fijar la posición de
desplazamiento en la ventana `<wsname>_FIND` (por ejemplo, con Mayús+clic),
pero también pueden ajustarse manualmente introduciendo las coordenadas. La
RA y la DEC pueden especificarse como valores decimales (grados) o en
notación sexagesimal.

Para centrar la imagen en el apuntado actual del telescopio, marque la
casilla junto a "Follow telescope" en la interfaz del complemento
``FindImage``. Esto le permitirá observar un dithering en una zona del cielo
si el WCS de la imagen de búsqueda es razonablemente preciso.

.. note:: Para que la función "Follow telescope" funcione, debe haber escrito
          un complemento acompañante que obtenga el estado de su telescopio,
          tal como se describe en la documentación del complemento
          TelescopePosition.
