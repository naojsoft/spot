CPanel
======
CPanel è il pannello di controllo (Control Panel) dell'applicazione SPOT.

Usa CPanel per avviare una nuova area di lavoro o per aprire i plugin di
pianificazione di SPOT in una specifica area di lavoro.

Creare un'area di lavoro
------------------------
Per aprire un'area di lavoro, scegline una dalla casella a discesa
modificabile (che viene popolata con le aree di lavoro trovate in
``$HOME/.spot/workspaces``) — oppure digitavi un nuovo nome — e premi il
pulsante "Open Workspace" alla sua destra. I nomi delle aree di lavoro devono
essere univoci. Se lasci la casella vuota, viene creata un'area di lavoro con
un nome generico.

Seleziona l'area di lavoro aperta scegliendone la scheda per vedere e
utilizzare i plugin che vi verranno aperti.

Selezionare un'area di lavoro per avviare un plugin
---------------------------------------------------
Usando il menu a discesa "Select Workspace", scegli un'area di lavoro aperta
in cui vuoi avviare uno dei plugin di pianificazione di SPOT (nota che l'area
di lavoro deve prima essere stata aperta con "Open Workspace"). Poi usa le
caselle di spunta qui sotto per avviare (spunta) o arrestare (togli la
spunta) un plugin.

Quasi sempre vorrai avviare il plugin "SiteSelector", perché controlla molti
degli aspetti degli altri plugin visibili nell'area di lavoro.

Suggerimento: ridurre a icona i plugin
--------------------------------------
A volte vuoi avviare un plugin per usarne alcune funzioni, ma potresti non
essere interessato a guardarne l'interfaccia (buoni esempi sono i plugin
"SiteSelector", "PolarSky" e "SkyCam"). In questi casi puoi avviare il plugin
e poi fare clic sul pulsante di riduzione a icona nella barra del titolo del
plugin per ridurlo a icona e liberare spazio per altri plugin.

.. important:: La chiusura di alcuni plugin può far sì che altri plugin non
               funzionino come previsto. Ad esempio, il plugin SiteSelector è
               importante come fonte degli aggiornamenti dell'orario per
               quasi tutti gli altri plugin, e se lo chiudi completamente il
               relativo tracciatore dell'orario potrebbe non attivare più gli
               aggiornamenti negli altri plugin. Nel dubbio, riduci a icona
               un plugin invece di chiuderlo.

Salvare la disposizione dell'area di lavoro
-------------------------------------------
Premendo il pulsante "Save <wsname> layout", salverai la dimensione e la
posizione attuali delle finestre dei plugin che hai aperto nell'area di
lavoro indicata, insieme ai plugin attualmente in esecuzione. La disposizione
di ciascuna area di lavoro viene salvata separatamente in
``$HOME/.spot/workspaces/<wsname>/workspace.json``.

Al successivo avvio di SPOT, aprendo un'area di lavoro con lo stesso nome,
essa ricreerà le finestre con le dimensioni e le posizioni salvate e
riavvierà i plugin che erano in esecuzione al momento del salvataggio.
