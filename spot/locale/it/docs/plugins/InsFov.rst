++++++++++++++
Instrument FOV
++++++++++++++

Il plugin Instrument FOV si usa per sovrapporre il campo visivo di uno
strumento a un'immagine di survey nella finestra `<wsname>_FIND`.

.. note:: È importante aver scaricato in precedenza nel visore di ricerca
          (usando il plugin "FindImage") un'immagine con un WCS accurato
          affinché questo plugin funzioni correttamente.

Selezionare lo strumento
========================

Lo strumento può essere selezionato premendo il pulsante "Choose" sotto
"Instrument" e poi navigando nel menu finché non trovi lo strumento
desiderato. Una volta selezionato lo strumento, il nome verrà inserito in
"Instrument:" e un contorno del campo visivo dello strumento apparirà nella
finestra `<wsname>_FIND`.

L'angolo di posizione può essere regolato, il che regolerà l'angolo della
sovrapposizione del FOV dello strumento sull'immagine. Se la casella "Rotate
w/PA" è spuntata, l'immagine del visore verrà ruotata in modo che la
sovrapposizione del FOV mantenga lo stesso orientamento.

La RA e la DEC verranno compilate automaticamente impostando la posizione di
spostamento nella finestra `<wsname>_FIND` (ad esempio con Maiusc+clic), ma
possono anche essere regolate manualmente inserendo le coordinate. La RA e la
DEC possono essere specificate come valori decimali (gradi) o in notazione
sessagesimale.

Per centrare l'immagine sul puntamento attuale del telescopio, spunta la
casella accanto a "Follow telescope" nell'interfaccia del plugin
``FindImage``. Questo ti permetterà di osservare un dithering in atto su
un'area del cielo se il WCS nell'immagine di ricerca è ragionevolmente
accurato.

.. note:: Per far funzionare la funzione "Follow telescope" devi aver scritto
          un plugin di accompagnamento che ottenga lo stato dal tuo
          telescopio, come descritto nella documentazione del plugin
          TelescopePosition.
