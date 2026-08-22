++++++++++++++++
Target Generator
++++++++++++++++

TargetGenerator ermöglicht es Ihnen, ein Ziel auf eine von mehreren Weisen
dynamisch zu erzeugen. Das Ziel kann anschließend zur Tabelle des Plugins
„Targets“ hinzugefügt werden.

.. note:: Stellen Sie sicher, dass auch das Plugin „Targets“ geöffnet ist, da
          es zusammen mit diesem Plugin verwendet wird.

Ein Ziel aus Azimut/Elevation erzeugen
======================================

Geben Sie einfach einen Azimut in das Feld „Az:“ und eine Elevation in das
Feld „El:“ ein. Klicken Sie auf „Gen Target“, um die AZ/EL-Koordinaten unter
Verwendung der eingestellten Zeit des Standorts in RA/DEC-Koordinaten
umzuwandeln. Dadurch werden die Felder „RA“, „DEC“, „Equinox“ und „Name“ im
nächsten Abschnitt gefüllt. Von dort aus können Sie das Ziel wie im nächsten
Abschnitt beschrieben hinzufügen.

Ein Ziel aus bekannten Koordinaten erzeugen
===========================================

Wenn RA/DEC-Koordinaten bekannt sind, können sie in die mit „RA“, „DEC“,
„Equinox“ und „Name“ bezeichneten Felder eingegeben werden. Die Werte können
in sexagesimaler Schreibweise oder in Grad angegeben werden.

.. note:: Auch die „SOSS-Schreibweise“ kann verwendet werden, wenn Sie das
          Paket „oscript“ installiert haben.

Klicken Sie auf „Add Target“, um das Ziel hinzuzufügen. Es erscheint in der
Zieltabelle des Plugins „Targets“. Wählen Sie es dort auf die übliche Weise
aus, um es in den Diagrammen „PolarSky“ oder „Visibility“ zu sehen.

Ein Ziel über einen Nameserver nachschlagen
===========================================

Ein Ziel kann über einen Nameserver (NED oder SIMBAD) mithilfe der
Steuerelemente im dritten Bereich nachgeschlagen werden. Wählen Sie einfach
Ihren Nameserver aus dem Auswahlfeld mit der Bezeichnung „Server“, geben Sie
einen Namen in das Feld „Name“ ein und klicken Sie auf „Search name“. Wird
das Objekt gefunden, füllt es die mit „RA“, „DEC“, „Equinox“ und „Name“
bezeichneten Felder im zweiten Abschnitt. Von dort aus können Sie das Ziel
durch Klicken auf die Schaltfläche „Add Target“ hinzufügen.
