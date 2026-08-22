SiteSelector
============
Il plugin SiteSelector si usa per selezionare il luogo da cui prevedi di
osservare, oltre all'orario di osservazione in quel luogo.

Quasi sempre vorrai avviare per primo questo plugin, perché controlla molti
degli aspetti degli altri plugin visibili nell'area di lavoro.

Impostare il luogo di osservazione
----------------------------------
Usa il menu a discesa "Site:" per selezionare il luogo di osservazione. Sono
disponibili diversi siti predefiniti.

Aggiungere un proprio luogo di osservazione personalizzato
----------------------------------------------------------
Se il luogo desiderato non è disponibile, puoi aggiungerlo facilmente da te.
Se hai il codice sorgente di SPOT scaricato, puoi trovare il file
"sites.yml" in .../spot/spot/config/. Copia questo file in $HOME/.spot e
modificalo per aggiungere il tuo sito. Assicurati di impostare tutte le
chiavi del tuo sito (latitudine, longitudine, altitudine, ecc.). Riavvia spot
e dovresti riuscire a vedere il tuo nuovo luogo.

Impostare l'orario di osservazione
----------------------------------
L'orario può essere impostato sull'ora corrente o su un orario fisso. Per
impostarlo sull'ora corrente, scegli "Now" dal menu a discesa "Time mode:".

Per impostare un orario fisso, scegli "Fixed": questo abiliterà i controlli
"Date time:" e "UTC offset (min):". Inserisci la data/ora nella prima casella
nel formato YYYY-MM-DD HH:MM:SS e premi "Set".

Per impostazione predefinita, lo scostamento UTC dell'orario fisso verrà
impostato su quello del fuso orario del luogo di osservazione; ma puoi
inserire uno scostamento personalizzato (in *minuti*) rispetto all'UTC
nell'altra casella e premere "Set" per indicare uno scostamento speciale con
cui interpretare l'orario.

.. note:: questo NON cambia il fuso orario del luogo di osservazione;
          imposta soltanto l'interpretazione dell'orario fisso che stai
          impostando.

Aggiornamento dei plugin
------------------------
Ogni volta che cambi il luogo di osservazione o l'orario, gli altri plugin
dovrebbero aggiornarsi automaticamente (se si sono sottoscritti alle
variazioni di sito e orario, come la maggior parte è progettata per fare).

.. important:: La chiusura di questo plugin può far sì che altri plugin non
               funzionino come previsto. SiteSelector è importante come fonte
               degli aggiornamenti dell'orario per quasi tutti gli altri
               plugin, e se lo chiudi completamente il relativo tracciatore
               dell'orario non attiverà più gli aggiornamenti negli altri
               plugin. Nel dubbio, avvia e riduci a icona questo plugin
               invece di chiuderlo.
