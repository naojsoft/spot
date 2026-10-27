++++++++
Sky Cams
++++++++

Das SkyCam-Plugin dient dazu, ein Bild einer Ganzhimmelkamera in den
Hintergrund des Targets-Kanals zu legen, um die Überwachung der
Himmelsbedingungen zu unterstützen. Es gibt ein Auswahlmenü mit mehreren
Standorten zur Auswahl.

Das Himmelsbild festlegen
=========================

Das Plugin hat zwei Reiter: Die unten beschriebenen Bedienelemente
befinden sich auf dem Reiter „Kamera“, und der Reiter „Verlauf“ zeigt die
Bewölkung im zeitlichen Verlauf (siehe „Bewölkungsverlauf“).

Wählen Sie im Auswahlmenü unter „Ganzhimmelkamera“ den Kameraserver, den Sie
verwenden möchten. Aktivieren Sie dann das Kontrollkästchen neben „Himmelsbild anzeigen“, um das Bild im Fenster `<wsname>_TGTS` anzuzeigen. Es kann einen
Moment dauern, bis das Himmelsbild erscheint. Wenn das Bild aktualisiert
wird, werden Datum und Uhrzeit des letzten Bildes unten im Fenster unter
„Bild-Download-Info“ angezeigt.

Manche Ganzhimmelkameras liefern Farbbilder. Wenn Sie das Kontrollkästchen
„Monochrom“ aktivieren, werden diese in ein monochromes (Graustufen-)Bild
umgewandelt; deaktivieren Sie es, um die Originalfarben anzuzeigen.

Das Himmelsbild wird mit der Farbtabelle und den Schnittwerten des
Betrachters gezeichnet, sodass Sie Kontrast und Schnittwerte mit den
üblichen Bedienelementen des Betrachters einstellen können (bei einem
Farbbild wirken nur die Schnittwerte). Ihre Einstellungen bleiben erhalten,
wenn neue Bilder eintreffen.

Differenzbild
=============

Aktivieren Sie das Kontrollkästchen neben „Differenzbild anzeigen“, um
statt des Bildes selbst anzuzeigen, wie sich der Himmel zwischen den beiden
letzten Bildern der Kamera verändert hat. So lassen sich ziehende oder sich
bildende Wolken viel leichter erkennen. Mit der voreingestellten Farbtabelle
„Grau“ erscheinen unveränderte Bereiche mittelgrau, heller gewordene
Bereiche heller und dunkler gewordene Bereiche dunkler. Wolken, die vom Mond
oder von Stadtlichtern beleuchtet werden, werden meist heller; Wolken, die
die Sterne oder die Milchstraße verdecken, werden dunkler.

Für das Differenzbild werden beide Bilder in Monochrom umgewandelt, in der
Auflösung reduziert und mit einem Medianfilter bearbeitet, der die meisten
Sterne und das Rauschen entfernt. Das vorherige Bild wird an die
Gesamthelligkeit des aktuellen angepasst, damit Änderungen der
Kamerabelichtung nicht wie Wolken aussehen. Anschließend wird die Differenz
durch eine Schätzung des Bildrauschens geteilt, sodass das Differenzbild in
Einheiten des Rauschens („Sigma“) angegeben ist.

Die Bedienelemente sind:

* „Himmelsdrehung ausgleichen“: Der Himmel dreht sich um etwa ein Viertelgrad pro Minute,
  daher bewegen sich die Sterne zwischen den Bildern. Ist diese Option
  aktiviert, wird das vorherige Bild um den Himmelspol auf den Zeitpunkt
  des aktuellen Bildes gedreht, sodass sich die Sterne aufheben und nur
  echte Veränderungen übrig bleiben. Dazu muss die Ausrichtung der Kamera in
  skycams.yml stimmen (siehe „Neue Kameras hinzufügen“). Im Kamerabild
  feststehende Objekte wie Kuppeln oder Bäume nahe dem Horizont können dann
  gekrümmte Streifen hinterlassen.

* „Schwellenwert“: Eine Veränderung von mehr als so vielen Sigma zählt für den
  Bewölkungsgrad als Wolke (Voreinstellung 5).

* „Farbtabelle“: die Farbtabelle für das Differenzbild. „Grau“ und „Veränderung“
  (das nur die Stärke der Veränderung zeigt, nicht ob es heller oder dunkler
  wurde) halten die Ziel-Overlays gut lesbar; „Petrol/Bernstein“ und „Blau/Rot“
  zeigen die Richtung der Veränderung farbig an.

* „Bewölkung“: der Prozentsatz des Himmels innerhalb von 75 Grad um den
  Zenit, der sich um mehr als den Schwellenwert verändert hat. Er erfasst
  Wolken, die sich zwischen den Bildern bewegen oder verändern; eine
  gleichmäßige Bewölkung, die sich nicht verändert, erscheint nicht.
  Solange die Sonne am Standort der Kamera weniger als 12 Grad unter dem
  Horizont steht, ändert sich die Himmelshelligkeit zu schnell, als dass
  der Wert aussagekräftig wäre; dann wird stattdessen „Dämmerung“ oder
  „Tag“ angezeigt. Die Bewölkung wird gemessen, sobald zwei Bilder
  vorliegen, auch wenn das Differenzbild nicht angezeigt wird.

Das Differenzbild behält eine eigene Farbtabelle und eigene Schnittwerte
(standardmäßig -10 bis +10 Sigma), getrennt von denen des normalen Bildes,
und auch diese können Sie mit den üblichen Bedienelementen des Betrachters
einstellen.

Nach der Auswahl einer Kamera erscheint das Differenzbild, sobald ein
zweites Bild empfangen wurde. Liefert ein Download dasselbe Bild wie der
vorherige (die Kamera hat sich noch nicht aktualisiert), wird es ignoriert.

Die Schaltfläche „Konfiguration speichern“ speichert Ihre aktuelle Auswahl
(Kameraserver, „Himmelsbild anzeigen“, „Differenzbild anzeigen“ und
„Monochrom“) für den Arbeitsbereich, sodass sie beim nächsten Öffnen
wiederhergestellt wird.

Bewölkungsverlauf
=================

Der Reiter „Verlauf“ zeigt die Bewölkung der letzten 12 Stunden, mit
Uhrzeiten in der Zeitzone des in SPOT ausgewählten Standorts. Für jedes neue
Bild der Kamera wird ein Punkt hinzugefügt, ob das Differenzbild angezeigt
wird oder nicht. Punkte aus der Dämmerung oder vom Tag werden hohl
gezeichnet, und die Linie ist unterbrochen, wo Bilder fehlen. Eine Änderung
des Schwellenwerts ändert nur den letzten Punkt. „Löschen“ leert den
Verlauf, der auch geleert wird, wenn Sie eine andere Kamera auswählen.

Neue Kameras hinzufügen
=======================

Sie können ganz einfach eigene Ganzhimmelkamera-Bilder hinzufügen, wenn Sie
über einen geeigneten Bild-Feed verfügen, der sich über Webprotokolle
abrufen lässt. Wenn Sie den SPOT-Quellcode ausgecheckt haben, finden Sie die
Datei „skycams.yml“ in .../spot/spot/config/. Kopieren Sie diese Datei nach
$HOME/.spot und bearbeiten Sie sie, um Ihre eigene Kamera hinzuzufügen. Sie
müssen eine URL zum Herunterladen der Bilder angeben, einen Titel, ein
Mittelpixel (X- und Y-Koordinaten) im Bild, das den Zenit darstellt, den
Radius des Kreises bis zum Horizont in Pixeln, eine anzuwendende Drehung, ob
das Bild in X- oder Y-Richtung gespiegelt werden soll, sowie ein
Aktualisierungsintervall in Sekunden. Sie können außerdem den Standort der
Kamera in Grad als „latitude“ (auf der Südhalbkugel negativ) und
„longitude“ (westlich von Greenwich negativ) angeben. Die Breite wird
verwendet, um im Differenzbild die Drehung des Himmels auszugleichen, und
beide zusammen, um festzustellen, wann es an der Kamera Nacht ist. Fehlen
sie, wird der Standort des in SPOT ausgewählten Ortes verwendet, was falsch
ist, wenn sich die Kamera an einem anderen Standort befindet.

Manche Kameras veröffentlichen nur ein animiertes Bild (etwa eine GIF-Schleife
der letzten Bilder). SPOT verwendet dann das letzte Bild der Animation, das
normalerweise das neueste ist; um ein anderes Bild zu verwenden, geben Sie
dessen Nummer als „frame“ an (ab 0 gezählt, oder ab -1 für das letzte).

Drehung und Spiegelungen müssen das Bild so ausrichten, dass Norden oben und
Osten links liegt, wie im polaren Himmelsdiagramm (auf beiden
Halbkugeln). Eine gute Kontrolle ist, dass der Mond oder ein heller Planet
im Himmelsbild mit seiner Position in SPOT übereinstimmt und dass sich die
Sterne im Differenzbild bei aktiviertem „Himmelsdrehung ausgleichen“ aufheben.

Starten Sie spot neu, dann sollten Sie Ihre neue Kamera aus der Liste
auswählen können.
