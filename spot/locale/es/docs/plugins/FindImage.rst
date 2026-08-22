FindImage
=========
El complemento FindImage se usa para descargar y mostrar imágenes de
catálogos de imágenes para coordenadas conocidas. Utiliza el visor
"{wsname}_FIND" para mostrar las imágenes encontradas.

.. note:: Asegúrese de tener también abierto el complemento "Targets", ya
          que se usa junto con este complemento.

Seleccionar un objetivo
-----------------------
En el complemento "Targets", seleccione un único objetivo para elegirlo de
forma inequívoca. Luego haga clic en el botón "Get Selected" del área
"Pointing" de FindImage. Esto debería rellenar los campos "RA", "DEC",
"Equinox" y "Name".

.. note:: Si dispone de una integración funcional del estado del telescopio,
          puede marcar la casilla "Follow telescope" para que el área
          "Pointing" se actualice con la posición real del telescopio, si
          coincide con un objetivo cargado en el complemento Targets. Además,
          la imagen en el visor de búsqueda se descargará y desplazará según
          la posición actual del telescopio, lo que le permite seguir (por
          ejemplo) un patrón de dithering.

Cargar una imagen desde una fuente de imágenes
----------------------------------------------
Una vez que las coordenadas RA/DEC se muestran en el área "Pointing", se
puede descargar una imagen usando los controles del área "Image Source".
Elija una fuente de imágenes en el control desplegable etiquetado "Source",
seleccione un tamaño (en arcominutos) con el control "Size" y haga clic en el
botón "Find Image". Puede tardar un poco en descargarse la imagen y mostrarse
en el visor de búsqueda.

.. note:: Alternativamente, "Load FITS" puede usarse para cargar un archivo
          FITS local con un WCS válido de la región, o puede hacer clic en
          "Create Blank" para crear una imagen en blanco con un WCS ajustado
          a la ubicación deseada. Cualquiera de estos puede ser útil si no
          hay una fuente de imágenes disponible por descarga.
