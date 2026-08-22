+++++++++++
Target List
+++++++++++

El complemento Targets se usa normalmente junto con los complementos
``PolarSky`` y ``Visibility`` para mostrar información sobre objetos celestes
que podrían observarse. Le permite cargar uno o varios archivos de objetivos
y luego trazarlos en la ventana "<wsname>_TGTS", o mostrar su visibilidad en
la interfaz del complemento ``Visibility``.

Cargar objetivos desde un archivo CSV
=====================================
Los objetivos pueden cargarse desde un archivo CSV que contenga un encabezado
con los títulos de columna "Name", "RA", "DEC" y "Equinox" (no es necesario
que estén en ese orden). Puede haber otras columnas, pero se ignorarán. En
este formato, la RA y la DEC pueden especificarse como valores decimales (en
cuyo caso se interpretan como grados) o en notación sexagesimal
(HH:MM:SS.SSS para la RA, DD:MM:SS.SS para la DEC). El Equinox puede
especificarse como, por ejemplo, J2000 o 2000.0.

.. note:: SPOT también puede leer objetivos de archivos CSV en "notación
          SOSS". Consulte la sección de abajo sobre la carga de objetivos
          desde un archivo OPE.

Si desea establecer un color específico para los objetivos que se van a
trazar, haga clic en el botón "Color" para seleccionar manualmente un color
antes de abrir un archivo; de lo contrario, los objetivos se colorearán según
la opción (descrita más abajo) llamada "Rotate target colors".

Pulse el botón "File" y navegue hasta seleccionar un archivo CSV con el
formato anterior. O escriba la ruta del archivo en el cuadro junto al botón
"File" y pulse "Set" (este último método también sirve para recargar
rápidamente un archivo que haya editado).

Los objetivos deberían rellenar la tabla.

Cargar objetivos desde un archivo OPE
=====================================
Un archivo OPE es un formato de archivo especial usado por el Telescopio
Subaru. Los objetivos de este tipo de archivo se especifican en "notación
SOSS" (HHMMSS.SSS para la RA, +|-DDMMSS.SS para la DEC, NNNN.0 para el
Equinox).

Siga las instrucciones anteriores para cargar objetivos desde un archivo CSV,
pero elija un archivo OPE en su lugar.

.. note:: Para poder cargar este formato necesita tener instalado el paquete
          opcional "oscript":
          (pip install git+https://github.com/naojsoft/oscript).

Subir archivos PRM
==================
Los archivos OPE suelen referenciar objetivos definidos en archivos "PRM"
separados. Seleccione (o arrastre y suelte) un archivo ``.prm`` de la misma
forma que haría con un archivo CSV u OPE: en lugar de cargar objetivos, se
guarda en ``~/.spot/prm`` (y se conserva) para que los archivos OPE cargados
posteriormente puedan resolver los objetivos que referencian.

Información de la tabla
=======================
La tabla de objetivos resume la información sobre los objetivos. Hay columnas
para información estática como el nombre del objetivo, RA, DEC, así como
información que se actualiza dinámicamente sobre azimut, altitud, un icono de
orto/ocaso codificado por colores, ángulo horario, masa de aire, dispersión
atmosférica, ángulo paraláctico y separación de la Luna.

Funcionamiento
==============
Para "marcar" objetivos, seleccione uno o varios objetivos de la lista y
pulse "Tag". Aparecerá una marca de verificación en el lado izquierdo, bajo
la columna "Tagged", para mostrar qué objetivos se han marcado. Para
desmarcar un objetivo, seleccione uno o varios objetivos marcados de la lista
y pulse "Untag".

En la ventana `<wsname>_TGTS`, los objetivos se trazarán en la posición
correspondiente a la hora establecida en el complemento SiteSelector. El
color del objetivo será de un tono magenta si el objetivo está marcado. Si un
objetivo está seleccionado, aparecerá en azul, y el nombre tendrá un fondo
blanco con un borde rojo en la ventana `<wsname>_TGTS`. De lo contrario, el
objetivo se coloreará según el color que se seleccionó manual o
automáticamente al cargar el archivo que contenía los objetivos.

El botón "Select All" seleccionará todos los objetivos de la tabla.

Seleccionar objetivos y pulsar "Delete" quitará los objetivos seleccionados
de la lista. Si solo se selecciona una fila de categoría (pero ningún
objetivo), al pulsar este botón se eliminarán todos los objetivos de la
categoría.

Seleccionar un único objetivo y luego hacer clic en "Browse" abrirá un menú
de opciones para buscar el objetivo por coordenada y presentar los resultados
en un navegador web.

El menú desplegable junto a "Plot:" cambia qué objetivos se trazan en la
ventana `<wsname>_TGTS`. Seleccionar "All" mostrará todos los objetivos,
seleccionar "Uncollapsed" mostrará los objetivos que no estén contraídos
(ocultos) en la tabla, así como los marcados y seleccionados, seleccionar
"Tagged+Selected" mostrará todos los objetivos que hayan sido marcados o
estén seleccionados, y seleccionar "Selected" mostrará solo los objetivos que
estén seleccionados.

Menú de ajustes
===============
Al hacer clic en el botón "Settings" se abrirá un menú emergente para
habilitar ciertos ajustes.

* Si marca "Merge Targets", todos los objetivos cargados *después de eso* se
  organizarán bajo un único encabezado llamado "Targets", en lugar de
  agruparse por nombre de archivo.
* "List Unreferenced Targets" es un ajuste que solo afecta a los archivos
  OPE. Normalmente, el complemento Targets ignora los objetivos que no se
  referencian en los comandos. Marcar este ajuste mostrará todos los
  objetivos, estén o no referenciados. Esto puede usarse para mostrar
  objetivos en archivos de inclusión PRM.
* Marcar la opción "Plot solar system objects" trazará el Sol, la Luna de la
  Tierra, los planetas y Plutón en la ventana `<wsname>_TGTS`.

* La opción "Rotate target colors" hará que cada archivo cargado use un color
  distinto seleccionado automáticamente para los objetivos (esto solo surtirá
  efecto si "Merge targets" está desactivado).
* "Enable DateTime setting" es una opción para habilitar el ajuste de una
  fecha/hora fija si el archivo CSV incluye una columna "DateTime". Cuando
  está habilitada, seleccionar un único objetivo en la tabla fijará la
  fecha/hora del complemento SiteSelector a esa fecha y hora. El formato de
  esta columna debe ser: YYYY-MM-DD HH:MM:SS <TZ>. Si se omite la cadena de
  la zona horaria, se asume UTC.
