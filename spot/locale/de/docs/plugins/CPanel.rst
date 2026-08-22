CPanel
======
CPanel ist das Bedienfeld (Control Panel) der SPOT-Anwendung.

Verwenden Sie CPanel, um einen neuen Arbeitsbereich zu starten oder um
SPOT-Planungs-Plugins in einem bestimmten Arbeitsbereich zu öffnen.

Einen Arbeitsbereich erstellen
------------------------------
Um einen Arbeitsbereich zu öffnen, wählen Sie einen aus dem bearbeitbaren
Auswahlfeld (es wird mit den in ``$HOME/.spot/workspaces`` gefundenen
Arbeitsbereichen gefüllt) – oder geben Sie einen neuen Namen ein – und
drücken Sie die Schaltfläche „Open Workspace“ rechts daneben. Die Namen der
Arbeitsbereiche müssen eindeutig sein. Wenn Sie das Feld leer lassen, wird
ein Arbeitsbereich mit einem generischen Namen erstellt.

Wählen Sie den geöffneten Arbeitsbereich über seine Registerkarte aus, um die
dort geöffneten Plugins zu sehen und mit ihnen zu arbeiten.

Einen Arbeitsbereich zum Starten eines Plugins auswählen
--------------------------------------------------------
Wählen Sie über das Auswahlmenü „Select Workspace“ einen geöffneten
Arbeitsbereich, in dem Sie eines der SPOT-Planungs-Plugins starten möchten
(beachten Sie, dass der Arbeitsbereich zuvor mit „Open Workspace“ geöffnet
worden sein muss). Verwenden Sie dann die Kontrollkästchen darunter, um ein
Plugin zu starten (ankreuzen) oder zu stoppen (abwählen).

Fast immer werden Sie das Plugin „SiteSelector“ starten wollen, da es viele
Aspekte der anderen im Arbeitsbereich sichtbaren Plugins steuert.

Tipp: Plugins minimieren
------------------------
Manchmal möchten Sie ein Plugin starten, um einige seiner Funktionen zu
nutzen, sind aber möglicherweise nicht daran interessiert, die
Plugin-Oberfläche anzusehen (gute Beispiele sind die Plugins „SiteSelector“,
„PolarSky“ und „SkyCam“). In solchen Fällen können Sie das Plugin starten und
dann auf die Schaltfläche zum Minimieren der Oberfläche in der Titelleiste des
Plugins klicken, um das Plugin zu minimieren und Platz für andere Plugins zu
schaffen.

.. important:: Das Schließen einiger Plugins kann dazu führen, dass andere
               Plugins nicht wie erwartet funktionieren. Zum Beispiel ist das
               Plugin SiteSelector als Quelle der Zeitaktualisierungen für
               fast alle anderen Plugins wichtig, und wenn Sie es vollständig
               schließen, löst dessen Zeitverfolgung möglicherweise keine
               Aktualisierungen mehr in diesen anderen Plugins aus. Im
               Zweifelsfall minimieren Sie ein Plugin, anstatt es zu
               schließen.

Das Arbeitsbereichs-Layout speichern
------------------------------------
Durch Drücken der Schaltfläche „Save <wsname> layout“ speichern Sie die
aktuelle Größe und Position der Plugin-Fenster, die Sie im angegebenen
Arbeitsbereich geöffnet haben, zusammen mit den derzeit laufenden Plugins.
Das Layout jedes Arbeitsbereichs wird separat in
``$HOME/.spot/workspaces/<wsname>/workspace.json`` gespeichert.

Wenn Sie SPOT das nächste Mal starten und einen Arbeitsbereich mit demselben
Namen öffnen, werden die Fenster in ihrer gespeicherten Größe und Position
neu erstellt und die Plugins neu gestartet, die beim Speichern liefen.
