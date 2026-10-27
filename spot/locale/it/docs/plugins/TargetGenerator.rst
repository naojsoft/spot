++++++++++++++++
Target Generator
++++++++++++++++

TargetGenerator ti permette di generare un target dinamicamente in uno di
diversi modi. Il target può poi essere aggiunto alla tabella del plugin
"Targets".

.. note:: Assicurati di avere aperto anche il plugin "Targets", poiché viene
          usato insieme a questo plugin.

Generare un target da azimut/elevazione
=======================================

Basta digitare un azimut nella casella "Az:" e un'elevazione nella casella
"El:". Fai clic su "Genera target" per convertire le coordinate AZ/EL in
coordinate RA/DEC usando l'orario impostato del sito. Questo popolerà le
caselle "AR", "DEC", "Equinozio" e "Nome" della sezione successiva. Da lì puoi
aggiungere il target come descritto nella sezione successiva.

Generare un target da coordinate note
=====================================

Se le coordinate RA/DEC sono note, possono essere digitate nelle caselle
etichettate "AR", "DEC", "Equinozio" e "Nome". I valori possono essere forniti
in notazione sessagesimale o in gradi.

.. note:: È possibile usare anche la "notazione SOSS" se hai installato il
          pacchetto "oscript".

Fai clic su "Aggiungi target" per aggiungere il target. Comparirà nella tabella
dei target del plugin "Targets". Selezionalo lì nel modo consueto per vederlo
nei grafici "PolarSky" o "Visibility".

Cercare un target su un name server
===================================

Un target può essere cercato tramite un name server (NED o SIMBAD) usando i
controlli della terza area. Basta selezionare il tuo name server dalla
casella a discesa etichettata "Server", digitare un nome nella casella "Nome"
e fare clic su "Cerca nome". Se l'oggetto viene trovato, popolerà le caselle
etichettate "AR", "DEC", "Equinozio" e "Nome" della seconda sezione. Da lì puoi
aggiungere il target facendo clic sul pulsante "Aggiungi target".
