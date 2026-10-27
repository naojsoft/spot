FindImage
=========
Il plugin FindImage si usa per scaricare e visualizzare immagini dai
cataloghi di immagini per coordinate note. Utilizza il visore "{wsname}_FIND"
per mostrare le immagini trovate.

.. note:: Assicurati di avere aperto anche il plugin "Targets", poiché viene
          usato insieme a questo plugin.

Selezionare un target
---------------------
Nel plugin "Targets", seleziona un singolo target per sceglierlo in modo
univoco. Poi fai clic sul pulsante "Ottieni selezionato" nell'area "Puntamento" di
FindImage. Questo dovrebbe popolare i campi "AR", "DEC", "Equinozio" e "Nome".

.. note:: Se disponi di un'integrazione funzionante dello stato del
          telescopio, puoi spuntare la casella "Segui il telescopio" per far
          aggiornare l'area "Puntamento" con la posizione reale del telescopio,
          se corrisponde a un target caricato nel plugin Targets. Inoltre,
          l'immagine nel visore di ricerca verrà scaricata e spostata in base
          alla posizione attuale del telescopio, permettendoti di seguire (ad
          esempio) uno schema di dithering.

Caricare un'immagine da una sorgente di immagini
------------------------------------------------
Una volta che le coordinate RA/DEC sono visualizzate nell'area "Puntamento", è
possibile scaricare un'immagine usando i controlli dell'area "Sorgente immagine".
Scegli una sorgente di immagini dal controllo a discesa etichettato "Sorgente",
seleziona una dimensione (in arcominuti) con il controllo "Dimensione (arcmin)" e fai clic
sul pulsante "Trova immagine". Potrebbe volerci un po' prima che l'immagine venga
scaricata e visualizzata nel visore di ricerca.

.. note:: In alternativa, si può usare "Carica FITS" per caricare un file FITS
          locale con un WCS valido della regione, oppure fare clic su "Crea vuota" per creare un'immagine vuota con un WCS impostato sulla
          posizione desiderata. Ciascuna di queste opzioni può essere utile
          se una sorgente di immagini non è disponibile tramite download.
