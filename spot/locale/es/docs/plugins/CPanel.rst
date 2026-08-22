CPanel
======
CPanel es el Panel de Control de la aplicación SPOT.

Use CPanel para abrir un nuevo espacio de trabajo o para abrir complementos
de planificación de SPOT en un espacio de trabajo concreto.

Crear un espacio de trabajo
---------------------------
Para abrir un espacio de trabajo, elija uno del cuadro desplegable editable
(se rellena con los espacios de trabajo encontrados en
``$HOME/.spot/workspaces``) —o escriba un nombre nuevo en él— y pulse el
botón "Open Workspace" situado a su derecha. Los nombres de los espacios de
trabajo deben ser únicos. Si deja el cuadro vacío, se crea un espacio de
trabajo con un nombre genérico.

Seleccione la pestaña del espacio de trabajo abierto para ver y trabajar con
los complementos que se abrirán allí.

Seleccionar un espacio de trabajo para iniciar un complemento
-------------------------------------------------------------
Con el menú desplegable "Select Workspace", elija un espacio de trabajo
abierto en el que desee iniciar uno de los complementos de planificación de
SPOT (tenga en cuenta que el espacio de trabajo debe haberse abierto primero
con "Open Workspace"). Luego use las casillas de abajo para iniciar (marcar)
o detener (desmarcar) un complemento.

Casi siempre querrá iniciar el complemento "SiteSelector", porque controla
muchos de los aspectos de los otros complementos visibles en el espacio de
trabajo.

Sugerencia: minimizar complementos
----------------------------------
A veces quiere iniciar un complemento para usar algunas de sus funciones,
pero puede que no le interese mirar su interfaz (buenos ejemplos son los
complementos "SiteSelector", "PolarSky" y "SkyCam"). En esos casos puede
iniciar el complemento y luego hacer clic en el botón de minimización de la
interfaz en la barra de título del complemento para minimizarlo y crear
espacio para otros complementos.

.. important:: Cerrar algunos complementos puede hacer que otros no funcionen
               como se espera. Por ejemplo, el complemento SiteSelector es
               importante como fuente de las actualizaciones de tiempo para
               casi todos los demás complementos, y si lo cierra por completo,
               su rastreador de tiempo puede dejar de activar las
               actualizaciones en esos otros complementos. En caso de duda,
               minimice un complemento en lugar de cerrarlo.

Guardar la disposición del espacio de trabajo
---------------------------------------------
Al pulsar el botón "Save <wsname> layout", guardará el tamaño y la posición
actuales de las ventanas de los complementos que haya abierto en ese espacio
de trabajo, junto con los complementos que se están ejecutando actualmente.
La disposición de cada espacio de trabajo se guarda por separado en
``$HOME/.spot/workspaces/<wsname>/workspace.json``.

La próxima vez que inicie SPOT y abra un espacio de trabajo con el mismo
nombre, recreará las ventanas con sus tamaños y posiciones guardados y
reiniciará los complementos que se estaban ejecutando cuando guardó.
