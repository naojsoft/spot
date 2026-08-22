++++++++++++++++++
Telescope Position
++++++++++++++++++

El complemento Telescope Position muestra las posiciones en vivo del
telescopio y las comandadas (del objetivo).

.. note:: Para usar correctamente este complemento, es necesario escribir un
          complemento acompañante personalizado que proporcione el estado
          necesario para dibujar estas posiciones. Si no creó tal
          complemento, parecerá que el telescopio está aparcado.

Las posiciones del telescopio y del objetivo se muestran tanto en Ascensión
Recta/Declinación como en Azimut/Elevación. La RA y la DEC se muestran en
notación sexagesimal como HH:MM:SS.SSS para la RA y DD:MM:SS.SS para la DEC.
El AZ y el EL se muestran ambos en grados como valores decimales. En la
sección "Telescope" se muestra el estado del telescopio, como apuntando o en
giro, junto con el tiempo de giro en h:mm:ss.

La opción "Plot telescope position" mostrará las posiciones del objetivo y
del telescopio en la ventana Targets cuando la casilla esté marcada.

La opción "Target follow telescope" hará que se seleccione un objetivo en la
tabla del complemento Targets cuando el telescopio esté "cerca" de ese
objetivo (definiéndose cerca como dentro de aproximadamente 10 arcominutos).
Se selecciona el objetivo real más cercano a la coordenada del telescopio.

.. note:: Si el usuario selecciona manualmente un objetivo después de marcar
          esta casilla, la opción se desmarcará automáticamente. Para
          restablecer el seguimiento del telescopio por parte del objetivo,
          simplemente vuelva a marcar la casilla.

La opción "Pan to telescope position" hará que el visor TGTS se desplace a la
posición del telescopio. Esto puede ser útil cuando hay muchos objetivos
trazados y ha ampliado para mostrar solo una parte del campo polar del cielo.

Escribir un complemento acompañante
===================================

Descargue el código fuente de SPOT y busque en la carpeta "spot/examples"
una plantilla de complemento llamada "TelescopePosition_Companion".
Modifíquela como se describe en la plantilla.
