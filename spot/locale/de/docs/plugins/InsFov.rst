++++++++++++++
Instrument FOV
++++++++++++++

Das Instrument-FOV-Plugin dient dazu, das Gesichtsfeld eines Instruments über
ein Durchmusterungsbild im Fenster `<wsname>_FIND` zu legen.

.. note:: Es ist wichtig, zuvor (mit dem Plugin „FindImage“) ein Bild mit
          einem genauen WCS in den Suchbetrachter heruntergeladen zu haben,
          damit dieses Plugin ordnungsgemäß funktioniert.

Das Instrument auswählen
========================

Das Instrument kann ausgewählt werden, indem Sie die Schaltfläche „Choose“
unter „Instrument“ drücken und dann durch das Menü navigieren, bis Sie das
gewünschte Instrument finden. Sobald das Instrument ausgewählt ist, wird der
Name in „Instrument:“ eingetragen, und ein Umriss des Gesichtsfelds des
Instruments erscheint im Fenster `<wsname>_FIND`.

Der Positionswinkel kann angepasst werden, wodurch der Winkel der FOV-Überlagerung
des Instruments auf dem Bild angepasst wird. Wenn das Kontrollkästchen
„Rotate w/PA“ aktiviert ist, wird das Betrachterbild so gedreht, dass die
FOV-Überlagerung dieselbe Ausrichtung beibehält.

RA und DEC werden automatisch ausgefüllt, indem Sie die Schwenkposition im
Fenster `<wsname>_FIND` festlegen (zum Beispiel per Umschalt+Klick), können
aber auch manuell durch Eingabe der Koordinaten angepasst werden. RA und DEC
können als Dezimalwerte (Grad) oder in sexagesimaler Schreibweise angegeben
werden.

Um das Bild auf die aktuelle Teleskopausrichtung zu zentrieren, aktivieren
Sie das Kontrollkästchen neben „Follow telescope“ in der Oberfläche des
Plugins ``FindImage``. Dadurch können Sie ein ablaufendes Dithering in einem
Himmelsbereich beobachten, sofern das WCS im Suchbild hinreichend genau ist.

.. note:: Damit die Funktion „Follow telescope“ funktioniert, müssen Sie ein
          Begleit-Plugin geschrieben haben, das den Status von Ihrem Teleskop
          abruft, wie in der Dokumentation des Plugins TelescopePosition
          beschrieben.
