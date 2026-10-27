FindImage
=========
Das FindImage-Plugin dient dazu, Bilder aus Bildkatalogen für bekannte
Koordinaten herunterzuladen und anzuzeigen. Es verwendet den Betrachter
„{wsname}_FIND“, um die gefundenen Bilder anzuzeigen.

.. note:: Stellen Sie sicher, dass auch das Plugin „Targets“ geöffnet ist, da
          es zusammen mit diesem Plugin verwendet wird.

Ein Ziel auswählen
------------------
Wählen Sie im Plugin „Targets“ ein einzelnes Ziel aus, um es eindeutig
festzulegen. Klicken Sie dann auf die Schaltfläche „Ausgewähltes abrufen“ im Bereich
„Ausrichtung“ von FindImage. Dadurch sollten die Felder „RA“, „DEC“, „Äquinoktium“
und „Name“ gefüllt werden.

.. note:: Wenn Sie über eine funktionierende Einbindung des Teleskopstatus
          verfügen, können Sie das Kontrollkästchen „Teleskop folgen“
          aktivieren, damit der Bereich „Ausrichtung“ anhand der tatsächlichen
          Teleskopposition aktualisiert wird, sofern diese mit einem in das
          Plugin Targets geladenen Ziel übereinstimmt. Außerdem wird das Bild
          im Suchbetrachter entsprechend der aktuellen Teleskopposition
          heruntergeladen und geschwenkt, sodass Sie (zum Beispiel) einem
          Dithering-Muster folgen können.

Ein Bild aus einer Bildquelle laden
-----------------------------------
Sobald die RA/DEC-Koordinaten im Bereich „Ausrichtung“ angezeigt werden, kann
mit den Steuerelementen im Bereich „Bildquelle“ ein Bild heruntergeladen
werden. Wählen Sie eine Bildquelle aus dem Auswahlfeld mit der Bezeichnung
„Quelle“, wählen Sie mit dem Steuerelement „Größe (Bogenmin.)“ eine Größe (in
Bogenminuten) und klicken Sie auf die Schaltfläche „Bild suchen“. Es kann
einen Moment dauern, bis das Bild heruntergeladen und im Suchbetrachter
angezeigt wird.

.. note:: Alternativ kann mit „FITS laden“ eine lokale FITS-Datei mit einem
          gültigen WCS der Region geladen werden, oder Sie klicken auf
          „Leeres erstellen“, um ein leeres Bild mit einem auf den gewünschten
          Ort gesetzten WCS zu erstellen. Beides kann nützlich sein, wenn
          keine Bildquelle zum Herunterladen verfügbar ist.
