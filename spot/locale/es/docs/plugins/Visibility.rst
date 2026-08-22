+++++++++++++++
Visibility Plot
+++++++++++++++

Esta ventana contiene una representación que muestra la altitud a lo largo
del tiempo de los objetivos seleccionados en su lista de objetivos.

.. note:: Esta ventana estará en blanco si no hay objetivos seleccionados.

Regiones resaltadas
===================

Las regiones amarillas de la parte superior e inferior son las zonas de
advertencia. En esas regiones las observaciones son difíciles debido a una
masa de aire elevada o a una elevación muy alta. Las líneas verticales rojas
discontinuas son las horas del ocaso y del orto del Sol en el sitio. La
región vertical naranja delimita el tiempo del Crepúsculo Civil, la región
vertical lavanda delimita el tiempo del Crepúsculo Náutico, y la región
vertical azul delimita el tiempo del Crepúsculo Astronómico. La región verde
marca la próxima hora a partir del momento actual.

Establecer el rango del gráfico
===============================

Para cambiar el intervalo de tiempo representado, pulse el botón etiquetado
"Time axis:" para abrir un menú desplegable. Hay tres opciones disponibles:
Night Center, Day Center y Current. "Night Center" centrará el eje temporal
en la mitad de la noche, que puede encontrarse en la ventana :doc:`polarsky`.
El eje temporal se extenderá desde un poco antes del ocaso hasta un poco
después del orto. "Day Center" centrará el eje temporal en la mitad del día,
y el eje temporal se extenderá del orto al ocaso. "Current" ajustará el eje
temporal para que se extienda desde unas -2 hasta +7 horas, y se ajustará
automáticamente a medida que pase el tiempo.

Selección de objetivos
======================

El menú desplegable junto a "Plot:" controla qué objetivos se trazan en el
gráfico de visibilidad. Seleccionar "All" mostrará todos los objetivos,
seleccionar "Uncollapsed" mostrará los objetivos que no estén contraídos
(ocultos) en la tabla de objetivos, así como los marcados y seleccionados,
seleccionar "Tagged+Selected" mostrará todos los objetivos que hayan sido
marcados o estén seleccionados, y seleccionar "Selected" mostrará solo los
objetivos que estén seleccionados.

Menú de ajustes
===============
Al hacer clic en el botón "Settings" se abrirá un menú emergente para
habilitar ciertos ajustes.

* Trazar la separación de la Luna. Al marcar esta opción se mostrará la
  separación en grados en cada hora a lo largo de cada línea de trazado
  mientras el objeto esté por encima del horizonte.
* Trazar Az/El polar. Al marcar esta opción se creará una línea en el visor
  "<wsname>_TGTS" que marca la posición de cada objetivo durante el periodo
  seleccionado para el eje temporal (ver arriba), y para los objetivos
  seleccionados por la selección de objetivos del gráfico. Esto le permite
  ver más que la posición del objetivo según la hora en SiteSelector.
