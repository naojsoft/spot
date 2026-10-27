++++++++
Sky Cams
++++++++

Il plugin SkyCam si usa per collocare un'immagine di una fotocamera all-sky
sullo sfondo del canale Targets, così da agevolare il monitoraggio delle
condizioni del cielo. È presente un menu a discesa con diversi siti tra cui
scegliere.

Impostare l'immagine del cielo
==============================

Selezionate il server della fotocamera che desiderate usare dal menu a
discesa sotto "Fotocamera all-sky". Quindi spuntate la casella accanto a "Mostra immagine del cielo" per visualizzare l'immagine nella finestra `<wsname>_TGTS`.
Potrebbe volerci qualche istante prima che l'immagine del cielo compaia.
Quando l'immagine si aggiorna, la data e l'ora dell'ultima immagine vengono
mostrate in fondo alla finestra, sotto "Info sul download dell'immagine".

Alcune fotocamere all-sky producono immagini a colori. Spuntando la casella
"Monocromatico" queste vengono convertite in un'immagine monocromatica (scala di
grigi); togliete la spunta per mostrare i colori originali.

L'immagine del cielo è disegnata con la mappa di colori e i livelli di taglio
del visualizzatore, quindi potete regolarne il contrasto e i livelli di
taglio con i consueti controlli del visualizzatore (per un'immagine a colori
valgono solo i livelli di taglio). Le vostre impostazioni vengono mantenute
quando arrivano nuove immagini.

Immagine differenziale
======================

Spuntate la casella accanto a "Mostra immagine differenziale" per mostrare come è
cambiato il cielo tra le ultime due immagini della fotocamera, invece
dell'immagine stessa. In questo modo le nubi che si spostano o si formano
sono molto più facili da vedere. Con la mappa di colori predefinita "Grigio",
le zone che non sono cambiate appaiono grigio medio, quelle diventate più
luminose sono più chiare e quelle diventate più scure sono più scure. Le
nubi illuminate dalla Luna o dalle luci delle città di solito diventano più
luminose; le nubi che nascondono le stelle o la Via Lattea diventano più
scure.

Per creare l'immagine differenziale, entrambe le immagini vengono convertite
in monocromatico, ridotte di risoluzione e filtrate con un filtro mediano,
che elimina la maggior parte delle stelle e del rumore. L'immagine
precedente viene scalata per uguagliare la luminosità complessiva di quella
attuale, in modo che le variazioni di esposizione della fotocamera non
sembrino nubi. La differenza viene poi divisa per una stima del rumore
dell'immagine, quindi l'immagine differenziale è espressa in unità del
rumore ("sigma").

I controlli sono:

* "Compensa rotazione del cielo": il cielo ruota di circa un quarto di grado al minuto,
  quindi le stelle si spostano da un'immagine all'altra. Con questa opzione
  spuntata, l'immagine precedente viene ruotata attorno al polo celeste fino
  all'ora dell'immagine attuale, così che le stelle si annullano e restano
  solo i cambiamenti reali. Ciò richiede che l'orientamento della fotocamera
  in skycams.yml sia corretto (vedere "Aggiungere nuove fotocamere"). Gli
  oggetti fissi nel campo della fotocamera, come cupole o alberi vicino
  all'orizzonte, possono allora lasciare delle strisce curve.

* "Soglia": una variazione maggiore di questo numero di sigma viene
  contata come nube per la copertura nuvolosa (valore predefinito 5).

* "Mappa di colori": la mappa di colori dell'immagine differenziale. "Grigio" e
  "Variazione" (che mostra solo l'entità della variazione, non se la zona è
  diventata più luminosa o più scura) mantengono leggibili le
  sovrapposizioni dei target; "Verde acqua/Ambra" e "Blu/Rosso" mostrano il verso
  della variazione con il colore.

* "Copertura nuvolosa": la percentuale di cielo entro 75 gradi dallo zenit che è
  cambiata più della soglia. Misura le nubi che si spostano o cambiano tra
  un'immagine e l'altra; un cielo coperto uniforme che non cambia non
  compare.

L'immagine differenziale mantiene una propria mappa di colori e propri
livelli di taglio (per impostazione predefinita da -10 a +10 sigma),
separati da quelli dell'immagine normale, e anche questi si possono regolare
con i consueti controlli del visualizzatore.

Dopo aver selezionato una fotocamera, l'immagine differenziale compare
quando è stata ricevuta una seconda immagine. Se un download restituisce la
stessa immagine del precedente (la fotocamera non si è ancora aggiornata),
viene ignorato.

Il pulsante "Salva configurazione" registra le vostre selezioni attuali (server della
fotocamera, "Mostra immagine del cielo", "Mostra immagine differenziale" e "Monocromatico") per
lo spazio di lavoro, così che vengano ripristinate alla successiva apertura.

Aggiungere nuove fotocamere
===========================

Potete aggiungere facilmente le immagini delle vostre fotocamere all-sky se
disponete di un flusso di immagini adatto che si possa scaricare tramite
protocolli web. Se avete scaricato il codice sorgente di SPOT, trovate il
file "skycams.yml" in .../spot/spot/config/. Copiate questo file in
$HOME/.spot e modificatelo per aggiungere la vostra fotocamera. Dovrete
indicare un URL per scaricare le immagini, un titolo, un pixel centrale
(coordinate X e Y) dell'immagine che rappresenti lo zenit, il raggio in
pixel del cerchio fino all'orizzonte, una rotazione da applicare, se
capovolgere l'immagine nelle dimensioni X o Y, e un intervallo di
aggiornamento misurato in secondi. Potete anche indicare la latitudine della
fotocamera in gradi (negativa nell'emisfero australe) come "latitude"; viene
usata per compensare la rotazione del cielo nell'immagine differenziale. Se
non è indicata, viene usata la latitudine del sito selezionato in SPOT, che
non è corretta se la fotocamera si trova in un altro sito.

La rotazione e i capovolgimenti devono orientare l'immagine in modo che il
nord sia in alto e l'est a sinistra, come nel grafico polare del cielo (in
entrambi gli emisferi). Un buon controllo è verificare che la Luna o un
pianeta luminoso nell'immagine del cielo coincida con la sua posizione in
SPOT, e che le stelle si annullino nell'immagine differenziale con "Compensa rotazione del cielo" spuntato.

Riavviate spot e dovreste poter scegliere la vostra nuova fotocamera
dall'elenco.
