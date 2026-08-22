++++++++
Sky Cams
++++++++

Das SkyCam-Plugin dient dazu, ein Bild einer Ganzhimmelkamera in den
Hintergrund des Targets-Kanals zu legen, um die Überwachung der
Himmelsbedingungen zu unterstützen. Es gibt ein Auswahlmenü mit mehreren
Standorten zur Auswahl.

Das Himmelsbild festlegen
=========================

Wählen Sie den gewünschten Kameraserver aus dem Auswahlmenü unter „All Sky
Camera“. Aktivieren Sie dann das Kontrollkästchen neben „Show Sky Image“, um
das Bild im Fenster `<wsname>_TGTS` anzuzeigen. Es kann einige Augenblicke
dauern, bis das Himmelsbild erscheint. Wenn das Bild aktualisiert wird,
werden die Uhrzeit und das Datum des letzten Bildes am unteren Rand des
Fensters unter „Image Download Info“ angezeigt.

Das SkyCam-Plugin kann außerdem ein Differenzbild aus dem ausgewählten
Kanalserver erzeugen, indem Sie das Kontrollkästchen neben „Show Differential
Image“ aktivieren.

Neue Kameras hinzufügen
=======================

Sie können leicht Ihre eigenen Ganzhimmelkamera-Bilder hinzufügen, wenn Sie
über einen geeigneten Bildstrom verfügen, der über Web-Protokolle abgerufen
werden kann. Wenn Sie den SPOT-Quellcode ausgecheckt haben, finden Sie die
Datei „skycams.yml“ in .../spot/spot/config/. Kopieren Sie diese Datei nach
$HOME/.spot und bearbeiten Sie sie, um Ihre eigene Kamera hinzuzufügen. Sie
müssen eine URL zum Herunterladen von Bildern, einen Titel, einen
Mittelpunktpixel (X- und Y-Koordinaten) im Bild, der den Zenit darstellt, den
Radius des Kreises bis zum Horizont in Pixeln, eine anzuwendende Drehung, ob
das Bild in X- oder Y-Richtung gespiegelt werden soll, und ein
Aktualisierungsintervall in Sekunden angeben.

Starten Sie spot neu, und Sie sollten Ihre neue Kamera aus der Liste
auswählen können.
