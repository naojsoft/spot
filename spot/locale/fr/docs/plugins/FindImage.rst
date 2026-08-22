FindImage
=========
Le module FindImage sert à télécharger et à afficher des images provenant de
catalogues d'images pour des coordonnées connues. Il utilise la visionneuse
« {wsname}_FIND » pour afficher les images trouvées.

.. note:: Assurez-vous d'avoir également ouvert le module « Targets », car il
          est utilisé conjointement avec ce module.

Sélectionner une cible
----------------------
Dans le module « Targets », sélectionnez une seule cible pour la choisir de
façon unique. Cliquez ensuite sur le bouton « Get Selected » dans la zone
« Pointing » de FindImage. Cela devrait remplir les champs « RA », « DEC »,
« Equinox » et « Name ».

.. note:: Si vous disposez d'une intégration fonctionnelle de l'état du
          télescope, vous pouvez cocher la case « Follow telescope » pour que
          la zone « Pointing » soit mise à jour selon la position réelle du
          télescope, si elle correspond à une cible chargée dans le module
          Targets. De plus, l'image de la visionneuse de recherche sera
          téléchargée et déplacée en fonction de la position actuelle du
          télescope, ce qui vous permet de suivre (par exemple) un motif de
          dithering.

Charger une image depuis une source d'images
--------------------------------------------
Une fois les coordonnées RA/DEC affichées dans la zone « Pointing », une
image peut être téléchargée à l'aide des commandes de la zone « Image
Source ». Choisissez une source d'images dans la commande déroulante
étiquetée « Source », sélectionnez une taille (en arcminutes) avec la
commande « Size » et cliquez sur le bouton « Find Image ». Le téléchargement
et l'affichage de l'image dans la visionneuse de recherche peuvent prendre un
peu de temps.

.. note:: Vous pouvez aussi utiliser « Load FITS » pour charger un fichier
          FITS local avec un WCS valide de la région, ou cliquer sur « Create
          Blank » pour créer une image vide avec un WCS réglé sur
          l'emplacement souhaité. L'une de ces options peut être utile si une
          source d'images n'est pas disponible au téléchargement.
