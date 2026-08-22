+++++++++++
Target List
+++++++++++

Das Targets-Plugin wird normalerweise zusammen mit den Plugins ``PolarSky``
und ``Visibility`` verwendet, um Informationen über beobachtbare
Himmelsobjekte anzuzeigen. Es ermöglicht Ihnen, eine oder mehrere Zieldateien
zu laden und sie dann im Fenster „<wsname>_TGTS“ einzuzeichnen oder ihre
Sichtbarkeit in der Oberfläche des Plugins ``Visibility`` anzuzeigen.

Ziele aus einer CSV-Datei laden
===============================
Ziele können aus einer CSV-Datei geladen werden, die eine Kopfzeile mit den
Spaltentiteln „Name“, „RA“, „DEC“ und „Equinox“ enthält (sie müssen nicht in
dieser Reihenfolge stehen). Weitere Spalten können vorhanden sein, werden
aber ignoriert. In diesem Format können RA und DEC als Dezimalwerte (in
welchem Fall sie als Grad interpretiert werden) oder in sexagesimaler
Schreibweise angegeben werden (HH:MM:SS.SSS für RA, DD:MM:SS.SS für DEC).
Equinox kann z. B. als J2000 oder 2000.0 angegeben werden.

.. note:: SPOT kann Ziele auch aus CSV-Dateien in „SOSS-Schreibweise“ lesen.
          Siehe den Abschnitt weiter unten über das Laden von Zielen aus
          einer OPE-Datei.

Wenn Sie eine bestimmte Farbe für die einzuzeichnenden Ziele festlegen
möchten, klicken Sie auf die Schaltfläche „Color“, um vor dem Öffnen einer
Datei manuell eine Farbe auszuwählen; andernfalls werden die Ziele gemäß der
(weiter unten beschriebenen) Option „Rotate target colors“ eingefärbt.

Drücken Sie die Schaltfläche „File“ und navigieren Sie zu einer CSV-Datei im
obigen Format und wählen Sie diese aus. Oder geben Sie den Pfad der Datei in
das Feld neben der Schaltfläche „File“ ein und drücken Sie „Set“ (die
letztere Methode kann auch verwendet werden, um eine von Ihnen bearbeitete
Datei schnell neu zu laden).

Die Ziele sollten die Tabelle füllen.

Ziele aus einer OPE-Datei laden
===============================
Eine OPE-Datei ist ein spezielles Dateiformat, das vom Subaru-Teleskop
verwendet wird. Ziele in dieser Art von Datei werden in „SOSS-Schreibweise“
angegeben (HHMMSS.SSS für RA, +|-DDMMSS.SS für DEC, NNNN.0 für Equinox).

Befolgen Sie die obigen Anweisungen zum Laden von Zielen aus einer CSV-Datei,
wählen Sie jedoch stattdessen eine OPE-Datei.

.. note:: Um dieses Format zu laden, müssen Sie das optionale Paket „oscript“
          installiert haben:
          (pip install git+https://github.com/naojsoft/oscript).

PRM-Dateien hochladen
=====================
OPE-Dateien verweisen häufig auf Ziele, die in separaten „PRM“-Dateien
definiert sind. Wählen Sie eine ``.prm``-Datei aus (oder ziehen Sie sie per
Drag-and-drop) auf dieselbe Weise wie eine CSV- oder OPE-Datei: Anstatt Ziele
zu laden, wird sie in ``~/.spot/prm`` gespeichert (und dauerhaft abgelegt),
damit anschließend geladene OPE-Dateien die von ihnen referenzierten Ziele
auflösen können.

Tabelleninformationen
=====================
Die Zieltabelle fasst Informationen über die Ziele zusammen. Es gibt Spalten
für statische Informationen wie Zielname, RA, DEC sowie für sich dynamisch
aktualisierende Informationen zu Azimut, Höhe, einem farbcodierten
Auf-/Untergangssymbol, Stundenwinkel, Luftmasse, atmosphärischer Dispersion,
parallaktischem Winkel und Mondabstand.

Bedienung
=========
Um Ziele zu „taggen“, wählen Sie ein oder mehrere Ziele in der Liste aus und
drücken Sie „Tag“. Auf der linken Seite unter der Spalte „Tagged“ erscheint
ein Häkchen, um anzuzeigen, welche Ziele getaggt wurden. Um das Tag eines
Ziels zu entfernen, wählen Sie ein oder mehrere getaggte Ziele in der Liste
aus und drücken Sie „Untag“.

Im Fenster `<wsname>_TGTS` werden die Ziele an der Position der im
SiteSelector-Plugin eingestellten Zeit eingezeichnet. Die Farbe des Ziels ist
magentaartig, wenn das Ziel getaggt ist. Ist ein Ziel ausgewählt, erscheint
es blau, und der Name hat im Fenster `<wsname>_TGTS` einen weißen Hintergrund
mit rotem Rand. Andernfalls wird das Ziel gemäß der Farbe eingefärbt, die
beim Laden der Datei mit den Zielen manuell oder automatisch ausgewählt
wurde.

Die Schaltfläche „Select All“ wählt alle Ziele in der Tabelle aus.

Das Auswählen von Zielen und Drücken von „Delete“ entfernt die ausgewählten
Ziele aus der Liste. Ist nur eine Kategoriezeile ausgewählt (aber keine
Ziele), löscht das Drücken dieser Schaltfläche alle Ziele der Kategorie.

Das Auswählen eines einzelnen Ziels und anschließende Klicken auf „Browse“
öffnet ein Optionsmenü, um das Ziel nach Koordinate nachzuschlagen und die
Ergebnisse in einem Webbrowser anzuzeigen.

Das Auswahlmenü neben „Plot:“ ändert, welche Ziele im Fenster `<wsname>_TGTS`
eingezeichnet werden. Die Auswahl von „All“ zeigt alle Ziele an, die Auswahl
von „Uncollapsed“ zeigt alle Ziele an, die in der Tabelle nicht eingeklappt
(ausgeblendet) sind, sowie die getaggten und ausgewählten Ziele, die Auswahl
von „Tagged+Selected“ zeigt alle Ziele an, die getaggt oder ausgewählt sind,
und die Auswahl von „Selected“ zeigt nur die ausgewählten Ziele an.

Einstellungsmenü
================
Ein Klick auf die Schaltfläche „Settings“ öffnet ein Popup-Menü zum
Aktivieren bestimmter Einstellungen.

* Wenn Sie „Merge Targets“ aktivieren, werden alle *danach* geladenen Ziele
  unter einer einzigen Überschrift namens „Targets“ organisiert, anstatt nach
  Dateiname gruppiert zu werden.
* „List Unreferenced Targets“ ist eine Einstellung, die nur OPE-Dateien
  betrifft. Normalerweise ignoriert das Targets-Plugin Ziele, die in den
  Befehlen nicht referenziert werden. Das Aktivieren dieser Einstellung zeigt
  alle Ziele an, unabhängig davon, ob sie referenziert werden oder nicht.
  Damit lassen sich Ziele in PRM-Include-Dateien anzeigen.
* Das Aktivieren der Option „Plot solar system objects“ zeichnet die Sonne,
  den Erdmond, die Planeten und Pluto im Fenster `<wsname>_TGTS` ein.

* Die Option „Rotate target colors“ bewirkt, dass jede geladene Datei eine
  andere automatisch ausgewählte Farbe für die Ziele verwendet (dies wirkt
  sich nur aus, wenn „Merge targets“ deaktiviert ist).
* „Enable DateTime setting“ ist eine Option, um das Festlegen eines festen
  Datums/einer festen Uhrzeit zu aktivieren, falls die CSV-Datei eine Spalte
  „DateTime“ enthält. Wenn aktiviert, setzt das Auswählen eines einzelnen
  Ziels in der Tabelle das Datum/die Uhrzeit im SiteSelector-Plugin auf
  dieses Datum und diese Uhrzeit. Das Format dieser Spalte sollte sein:
  YYYY-MM-DD HH:MM:SS <TZ>. Wird die Zeitzonen-Zeichenkette weggelassen, wird
  UTC angenommen.
