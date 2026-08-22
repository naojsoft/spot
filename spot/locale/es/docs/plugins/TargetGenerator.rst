++++++++++++++++
Target Generator
++++++++++++++++

TargetGenerator le permite generar un objetivo dinámicamente de varias
maneras. El objetivo puede añadirse luego a la tabla del complemento
"Targets".

.. note:: Asegúrese de tener también abierto el complemento "Targets", ya
          que se usa junto con este complemento.

Generar un objetivo a partir de azimut/elevación
================================================

Simplemente escriba un azimut en el cuadro "Az:" y una elevación en el cuadro
"El:". Haga clic en "Gen Target" para convertir las coordenadas AZ/EL en
coordenadas RA/DEC usando la hora establecida del sitio. Esto rellenará los
cuadros "RA", "DEC", "Equinox" y "Name" de la siguiente sección. Desde ahí
puede añadir el objetivo como se describe en la siguiente sección.

Generar un objetivo a partir de coordenadas conocidas
=====================================================

Si se conocen las coordenadas RA/DEC, pueden escribirse en los cuadros
etiquetados "RA", "DEC", "Equinox" y "Name". Los valores pueden darse en
notación sexagesimal o en grados.

.. note:: También puede usarse la "notación SOSS" si tiene instalado el
          paquete "oscript".

Haga clic en "Add Target" para añadir el objetivo. Aparecerá en la tabla de
objetivos del complemento "Targets". Selecciónelo allí de la forma habitual
para verlo en los gráficos de "PolarSky" o "Visibility".

Buscar un objetivo en un servidor de nombres
============================================

Un objetivo puede buscarse mediante un servidor de nombres (NED o SIMBAD)
usando los controles de la tercera área. Simplemente seleccione su servidor
de nombres en el cuadro desplegable etiquetado "Server", escriba un nombre en
el cuadro "Name" y haga clic en "Search name". Si se encuentra el objeto,
rellenará los cuadros etiquetados "RA", "DEC", "Equinox" y "Name" de la
segunda sección. Desde ahí puede añadir el objetivo haciendo clic en el botón
"Add Target".
