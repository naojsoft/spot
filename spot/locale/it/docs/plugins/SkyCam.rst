++++++++
Sky Cams
++++++++

Il plugin SkyCam si usa per collocare un'immagine di una fotocamera all-sky
sullo sfondo del canale Targets, così da agevolare il monitoraggio delle
condizioni del cielo. È presente un menu a discesa con diversi siti tra cui
scegliere.

Impostare l'immagine del cielo
==============================

Seleziona il server della fotocamera che desideri usare dal menu a discesa
sotto "All Sky Camera". Poi spunta la casella accanto a "Show Sky Image" per
visualizzare l'immagine nella finestra `<wsname>_TGTS`. Potrebbero volerci
alcuni istanti prima che l'immagine del cielo compaia. Quando l'immagine si
aggiorna, l'ora e la data dell'ultima immagine verranno visualizzate in fondo
alla finestra, sotto "Image Download Info".

Il plugin SkyCam può anche generare un'immagine differenziale dal server di
canale selezionato spuntando la casella accanto a "Show Differential Image".

Aggiungere nuove fotocamere
===========================

Puoi aggiungere facilmente le tue immagini di fotocamera all-sky se disponi
di un flusso adeguato di immagini che possano essere recuperate tramite
protocolli web. Se hai il codice sorgente di SPOT scaricato, puoi trovare il
file "skycams.yml" in .../spot/spot/config/. Copia questo file in $HOME/.spot
e modificalo per aggiungere la tua fotocamera. Dovrai fornire un URL per
scaricare le immagini, un titolo, un pixel centrale (coordinate X e Y)
nell'immagine che rappresenti lo zenit, il raggio del cerchio fino
all'orizzonte in pixel, una rotazione da applicare, se ribaltare l'immagine
nelle dimensioni X o Y, e un intervallo di aggiornamento misurato in secondi.

Riavvia spot e dovresti riuscire a scegliere la tua nuova fotocamera
dall'elenco.
