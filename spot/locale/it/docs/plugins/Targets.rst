+++++++++++
Target List
+++++++++++

Il plugin Targets si usa normalmente insieme ai plugin ``PolarSky`` e
``Visibility`` per mostrare informazioni sugli oggetti celesti che potrebbero
essere osservati. Ti permette di caricare uno o più file di target e poi
tracciarli nella finestra "<wsname>_TGTS", oppure mostrarne la visibilità
nell'interfaccia del plugin ``Visibility``.

Caricare target da un file CSV
==============================
I target possono essere caricati da un file CSV che contiene un'intestazione
di colonna con i titoli "Name", "RA", "DEC" ed "Equinox" (non è necessario
che siano in quest'ordine). Possono essere presenti altre colonne, ma
verranno ignorate. In questo formato, la RA e la DEC possono essere
specificate come valori decimali (nel qual caso vengono interpretati come
gradi) o in notazione sessagesimale (HH:MM:SS.SSS per la RA, DD:MM:SS.SS per
la DEC). L'Equinox può essere specificato ad esempio come J2000 o 2000.0.

.. note:: SPOT può anche leggere target da file CSV in "notazione SOSS".
          Vedi la sezione sottostante sul caricamento dei target da un file
          OPE.

Se vuoi impostare un colore specifico per i target da tracciare, fai clic sul
pulsante "Color" per selezionare manualmente un colore prima di procedere ad
aprire un file, altrimenti i target verranno colorati in base all'opzione
(descritta più avanti) chiamata "Rotate target colors".

Premi il pulsante "File" e naviga fino a selezionare un file CSV con il
formato sopra indicato. Oppure digita il percorso del file nella casella
accanto al pulsante "File" e premi "Set" (quest'ultimo metodo può essere
usato anche per ricaricare rapidamente un file che hai modificato).

I target dovrebbero popolare la tabella.

Caricare target da un file OPE
==============================
Un file OPE è un formato di file speciale usato dal Telescopio Subaru. I
target in questo tipo di file sono specificati in "notazione SOSS"
(HHMMSS.SSS per la RA, +|-DDMMSS.SS per la DEC, NNNN.0 per l'Equinox).

Segui le istruzioni sopra per caricare i target da un file CSV, ma scegli un
file OPE invece.

.. note:: Per poter caricare questo formato devi avere installato il
          pacchetto opzionale "oscript":
          (pip install git+https://github.com/naojsoft/oscript).

Caricare file PRM
=================
I file OPE spesso fanno riferimento a target definiti in file "PRM"
separati. Seleziona (o trascina e rilascia) un file ``.prm`` nello stesso
modo in cui faresti con un file CSV o OPE: invece di caricare target, viene
salvato in ``~/.spot/prm`` (e reso persistente) in modo che i file OPE
caricati successivamente possano risolvere i target a cui fanno riferimento.

Informazioni della tabella
==========================
La tabella dei target riassume le informazioni sui target. Ci sono colonne
per informazioni statiche come nome del target, RA, DEC, oltre a informazioni
che si aggiornano dinamicamente per azimut, altitudine, un'icona di
sorgere/tramonto codificata a colori, angolo orario, massa d'aria,
dispersione atmosferica, angolo parallattico e separazione dalla Luna.

Funzionamento
=============
Per "contrassegnare" i target, seleziona uno o più target nell'elenco e premi
"Tag". Un segno di spunta comparirà sul lato sinistro sotto la colonna
"Tagged" per mostrare quali target sono stati contrassegnati. Per rimuovere
il contrassegno da un target, seleziona uno o più target contrassegnati
nell'elenco e premi "Untag".

Nella finestra `<wsname>_TGTS`, i target verranno tracciati nella posizione
corrispondente all'orario impostato nel plugin SiteSelector. Il colore del
target sarà di una tonalità simile al magenta se il target è contrassegnato.
Se un target è selezionato apparirà in blu, e il nome avrà uno sfondo bianco
con un bordo rosso nella finestra `<wsname>_TGTS`. Altrimenti il target verrà
colorato in base al colore selezionato manualmente o automaticamente al
momento del caricamento del file contenente i target.

Il pulsante "Select All" selezionerà tutti i target della tabella.

Selezionando dei target e premendo "Delete" verranno rimossi i target
selezionati dall'elenco. Se è selezionata solo una riga di categoria (ma
nessun target), premendo questo pulsante verranno eliminati tutti i target
della categoria.

Selezionando un singolo target e facendo poi clic su "Browse" si aprirà un
menu di opzioni per cercare il target per coordinata e presentare i risultati
in un browser web.

Il menu a discesa accanto a "Plot:" cambia quali target vengono tracciati
nella finestra `<wsname>_TGTS`. Selezionando "All" verranno mostrati tutti i
target, selezionando "Uncollapsed" verranno mostrati i target non compressi
(nascosti) nella tabella, oltre a quelli contrassegnati e selezionati,
selezionando "Tagged+Selected" verranno mostrati tutti i target che sono
stati contrassegnati o sono selezionati, e selezionando "Selected" verranno
mostrati solo i target selezionati.

Menu delle impostazioni
=======================
Facendo clic sul pulsante "Settings" verrà aperto un menu a comparsa per
abilitare determinate impostazioni.

* Se spunti "Merge Targets", tutti i target caricati *dopo di ciò* verranno
  organizzati sotto un'unica intestazione chiamata "Targets", invece di
  essere raggruppati per nome di file.
* "List Unreferenced Targets" è un'impostazione che riguarda solo i file OPE.
  Normalmente, il plugin Targets ignora i target che non sono referenziati
  nei comandi. Spuntando questa impostazione verranno mostrati tutti i target
  indipendentemente dal fatto che siano referenziati o meno. Questo può
  essere usato per mostrare i target nei file di inclusione PRM.
* Spuntando l'opzione "Plot solar system objects" verranno tracciati il Sole,
  la Luna della Terra, i pianeti e Plutone nella finestra `<wsname>_TGTS`.

* L'opzione "Rotate target colors" farà sì che ogni file caricato usi un
  diverso colore selezionato automaticamente per i target (questo avrà
  effetto solo se "Merge targets" è disattivato).
* "Enable DateTime setting" è un'opzione per abilitare l'impostazione di una
  data/ora fissa se il file CSV include una colonna "DateTime". Quando è
  abilitata, selezionando un singolo target nella tabella si imposterà la
  data/ora nel plugin SiteSelector su quella data e ora. Il formato di questa
  colonna dovrebbe essere: YYYY-MM-DD HH:MM:SS <TZ>. Se la stringa del fuso
  orario viene omessa, si assume UTC.
