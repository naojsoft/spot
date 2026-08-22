++++++++++++++++++
Telescope Position
++++++++++++++++++

Das Telescope-Position-Plugin zeigt die Live-Positionen des Teleskops und die
kommandierten (Ziel-)Positionen an.

.. note:: Um dieses Plugin erfolgreich zu nutzen, ist es erforderlich, ein
          eigenes Begleit-Plugin zu schreiben, das den zum Zeichnen dieser
          Positionen nötigen Status bereitstellt. Wenn Sie kein solches
          Plugin erstellt haben, sieht es so aus, als sei das Teleskop
          geparkt.

Die Positionen von Teleskop und Ziel werden sowohl in Rektaszension/Deklination
als auch in Azimut/Elevation angezeigt. RA und DEC werden in sexagesimaler
Schreibweise als HH:MM:SS.SSS für RA und DD:MM:SS.SS für DEC angezeigt. AZ und
EL werden beide in Grad als Dezimalwerte angezeigt. Im Abschnitt „Telescope“
wird der Teleskopstatus, etwa Ausrichten oder Schwenken, zusammen mit der
Schwenkzeit im Format h:mm:ss angezeigt.

Die Option „Plot telescope position“ zeigt die Ziel- und Teleskoppositionen
im Targets-Fenster an, wenn das Kontrollkästchen aktiviert ist.

Die Option „Target follow telescope“ bewirkt, dass in der Tabelle des Plugins
Targets ein Ziel ausgewählt wird, wenn das Teleskop diesem Ziel „nahe“ ist
(nahe ist definiert als innerhalb von etwa 10 Bogenminuten). Das der
Teleskopkoordinate tatsächlich nächstgelegene Ziel wird ausgewählt.

.. note:: Wenn der Benutzer nach dem Aktivieren dieses Kästchens manuell ein
          Ziel auswählt, wird die Option automatisch abgewählt. Um die
          Zielverfolgung des Teleskops wiederherzustellen, aktivieren Sie
          einfach das Kästchen erneut.

Die Option „Pan to telescope position“ bewirkt, dass der TGTS-Betrachter zur
Teleskopposition schwenkt. Das kann hilfreich sein, wenn viele Ziele
eingezeichnet sind und Sie hineingezoomt haben, um nur einen Teil des polaren
Himmelsfelds anzuzeigen.

Ein Begleit-Plugin schreiben
============================

Laden Sie den SPOT-Quellcode herunter und suchen Sie im Ordner
„spot/examples“ nach einer Plugin-Vorlage namens
„TelescopePosition_Companion“. Passen Sie sie wie in der Vorlage beschrieben
an.
