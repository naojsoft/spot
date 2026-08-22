++++++++++++++++++
Telescope Position
++++++++++++++++++

Il plugin Telescope Position visualizza le posizioni in tempo reale del
telescopio e quelle comandate (del target).

.. note:: Per usare correttamente questo plugin è necessario scrivere un
          plugin di accompagnamento personalizzato che fornisca lo stato
          necessario a disegnare queste posizioni. Se non hai creato un tale
          plugin, sembrerà che il telescopio sia in stazionamento.

Le posizioni del telescopio e del target sono mostrate sia in Ascensione
Retta/Declinazione sia in Azimut/Elevazione. La RA e la DEC sono visualizzate
in notazione sessagesimale come HH:MM:SS.SSS per la RA e DD:MM:SS.SS per la
DEC. L'AZ e l'EL sono entrambi visualizzati in gradi come valori decimali.
Nella sezione "Telescope" viene mostrato lo stato del telescopio, come
puntamento o spostamento, insieme al tempo di spostamento in h:mm:ss.

L'opzione "Plot telescope position" mostrerà le posizioni del target e del
telescopio nella finestra Targets quando la casella è selezionata.

L'opzione "Target follow telescope" farà sì che venga selezionato un target
nella tabella del plugin Targets quando il telescopio è "vicino" a quel
target (vicino essendo definito come entro circa 10 arcominuti). Viene
selezionato il target reale più vicino alla coordinata del telescopio.

.. note:: Se dopo aver spuntato questa casella l'utente seleziona
          manualmente un target, l'opzione verrà deselezionata
          automaticamente. Per ripristinare l'inseguimento del telescopio da
          parte del target, basta rispuntare la casella.

L'opzione "Pan to telescope position" farà sì che il visore TGTS si sposti
sulla posizione del telescopio. Questo può essere utile quando sono tracciati
molti target e hai ingrandito per mostrare solo una parte del campo polare
del cielo.

Scrivere un plugin di accompagnamento
=====================================

Scarica il codice sorgente di SPOT e cerca nella cartella "spot/examples" un
modello di plugin chiamato "TelescopePosition_Companion". Modificalo come
descritto nel modello.
