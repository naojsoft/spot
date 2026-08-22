SiteSelector
============
Das SiteSelector-Plugin dient dazu, den Ort auszuwählen, von dem aus Sie
beobachten möchten, sowie die Beobachtungszeit an diesem Ort.

Fast immer werden Sie dieses Plugin zuerst starten wollen, da es viele
Aspekte der anderen im Arbeitsbereich sichtbaren Plugins steuert.

Den Beobachtungsort festlegen
-----------------------------
Verwenden Sie das Auswahlmenü „Site:“, um den Beobachtungsort auszuwählen. Es
stehen mehrere vordefinierte Standorte zur Verfügung.

Einen eigenen benutzerdefinierten Beobachtungsort hinzufügen
------------------------------------------------------------
Wenn der gewünschte Ort nicht verfügbar ist, können Sie leicht Ihren eigenen
hinzufügen. Wenn Sie den SPOT-Quellcode ausgecheckt haben, finden Sie die
Datei „sites.yml“ in .../spot/spot/config/. Kopieren Sie diese Datei nach
$HOME/.spot und bearbeiten Sie sie, um Ihren eigenen Standort hinzuzufügen.
Achten Sie darauf, alle Schlüssel für Ihren Standort festzulegen
(Breitengrad, Längengrad, Höhe usw.). Starten Sie spot neu, und Sie sollten
Ihren neuen Ort sehen können.

Die Beobachtungszeit festlegen
------------------------------
Die Zeit kann auf die aktuelle Zeit oder eine feste Zeit gesetzt werden. Um
sie auf die aktuelle Zeit zu setzen, wählen Sie „Now“ aus dem Auswahlmenü
„Time mode:“.

Um eine feste Zeit festzulegen, wählen Sie „Fixed“ – dadurch werden die
Steuerelemente „Date time:“ und „UTC offset (min):“ aktiviert. Geben Sie
Datum/Uhrzeit im ersten Feld im Format YYYY-MM-DD HH:MM:SS ein und drücken
Sie „Set“.

Standardmäßig wird der UTC-Versatz der festen Zeit auf den der Zeitzone des
Beobachtungsorts gesetzt; Sie können jedoch im anderen Feld einen
benutzerdefinierten Versatz (in *Minuten*) gegenüber UTC eingeben und „Set“
drücken, um einen speziellen Versatz für die Interpretation der Zeit
anzugeben.

.. note:: dies ändert NICHT die Zeitzone des Beobachtungsorts; es legt nur
          die Interpretation der festen Zeit fest, die Sie einstellen.

Aktualisierung der Plugins
--------------------------
Immer wenn Sie den Beobachtungsort oder die Zeit ändern, sollten sich die
anderen Plugins automatisch aktualisieren (sofern sie Standort- und
Zeitänderungen abonnieren, wozu die meisten ausgelegt sind).

.. important:: Das Schließen dieses Plugins kann dazu führen, dass andere
               Plugins nicht wie erwartet funktionieren. SiteSelector ist als
               Quelle der Zeitaktualisierungen für fast alle anderen Plugins
               wichtig, und wenn Sie es vollständig schließen, löst dessen
               Zeitverfolgung keine Aktualisierungen mehr in diesen anderen
               Plugins aus. Im Zweifelsfall starten und minimieren Sie dieses
               Plugin, anstatt es zu schließen.
