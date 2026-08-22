++++++++++++++++++
Telescope Position
++++++++++++++++++

Le module Telescope Position affiche les positions en direct du télescope et
les positions commandées (de la cible).

.. note:: Pour utiliser ce module avec succès, il est nécessaire d'écrire un
          module compagnon personnalisé qui fournit l'état nécessaire au
          tracé de ces positions. Si vous n'avez pas créé un tel module, tout
          se passera comme si le télescope était garé.

Les positions du télescope et de la cible sont indiquées à la fois en
Ascension droite/Déclinaison et en Azimut/Élévation. La RA et la DEC sont
affichées en notation sexagésimale sous la forme HH:MM:SS.SSS pour la RA et
DD:MM:SS.SS pour la DEC. L'AZ et l'EL sont tous deux affichés en degrés sous
forme de valeurs décimales. Dans la section « Telescope », l'état du
télescope, tel que pointage ou déplacement, est affiché avec la durée de
déplacement au format h:mm:ss.

L'option « Plot telescope position » affichera les positions de la cible et
du télescope dans la fenêtre Targets lorsque la case est cochée.

L'option « Target follow telescope » entraînera la sélection d'une cible dans
la table du module Targets lorsque le télescope est « proche » de cette cible
(proche étant défini comme à moins d'environ 10 arcminutes). La cible réelle
la plus proche de la coordonnée du télescope est sélectionnée.

.. note:: Si une cible est sélectionnée manuellement par l'utilisateur après
          avoir coché cette case, l'option sera automatiquement décochée. Pour
          rétablir le suivi du télescope par la cible, il suffit de recocher
          la case.

L'option « Pan to telescope position » entraînera le déplacement de la
visionneuse TGTS vers la position du télescope. Cela peut être utile lorsque
de nombreuses cibles sont tracées et que vous avez zoomé pour n'afficher
qu'une partie du champ céleste polaire.

Écrire un module compagnon
==========================

Téléchargez le code source de SPOT et cherchez dans le dossier
« spot/examples » un modèle de module nommé « TelescopePosition_Companion ».
Modifiez-le comme décrit dans le modèle.
