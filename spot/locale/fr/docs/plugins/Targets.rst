+++++++++++
Target List
+++++++++++

Le module Targets est normalement utilisé conjointement avec les modules
``PolarSky`` et ``Visibility`` pour afficher des informations sur les objets
célestes qui pourraient être observés. Il vous permet de charger un ou
plusieurs fichiers de cibles puis de les tracer dans la fenêtre
« <wsname>_TGTS », ou d'afficher leur visibilité dans l'interface du module
``Visibility``.

Charger des cibles depuis un fichier CSV
========================================
Les cibles peuvent être chargées depuis un fichier CSV comportant un en-tête
de colonnes avec les titres « Name », « RA », « DEC » et « Equinox » (ils
n'ont pas besoin d'être dans cet ordre). D'autres colonnes peuvent être
présentes mais seront ignorées. Dans ce format, la RA et la DEC peuvent être
spécifiées en valeurs décimales (auquel cas elles sont interprétées en
degrés) ou en notation sexagésimale (HH:MM:SS.SSS pour la RA, DD:MM:SS.SS
pour la DEC). L'Equinox peut être spécifié par exemple comme J2000 ou 2000.0.

.. note:: SPOT peut aussi lire des cibles depuis des fichiers CSV en
          « notation SOSS ». Voir la section ci-dessous sur le chargement de
          cibles depuis un fichier OPE.

Si vous souhaitez définir une couleur spécifique pour les cibles à tracer,
cliquez sur le bouton « Color » pour sélectionner manuellement une couleur
avant de procéder à l'ouverture d'un fichier ; sinon, les cibles seront
colorées selon l'option (décrite plus bas) nommée « Rotate target colors ».

Appuyez sur le bouton « File » et naviguez jusqu'à sélectionner un fichier
CSV au format ci-dessus. Ou saisissez le chemin du fichier dans la case à
côté du bouton « File » et appuyez sur « Set » (cette dernière méthode peut
aussi servir à recharger rapidement un fichier que vous avez modifié).

Les cibles devraient remplir la table.

Charger des cibles depuis un fichier OPE
========================================
Un fichier OPE est un format de fichier spécial utilisé par le télescope
Subaru. Les cibles dans ce type de fichier sont spécifiées en « notation
SOSS » (HHMMSS.SSS pour la RA, +|-DDMMSS.SS pour la DEC, NNNN.0 pour
l'Equinox).

Suivez les instructions ci-dessus pour charger des cibles depuis un fichier
CSV, mais choisissez plutôt un fichier OPE.

.. note:: Pour pouvoir charger ce format, vous devez avoir installé le paquet
          optionnel « oscript » :
          (pip install git+https://github.com/naojsoft/oscript).

Téléverser des fichiers PRM
===========================
Les fichiers OPE référencent souvent des cibles définies dans des fichiers
« PRM » distincts. Sélectionnez (ou glissez-déposez) un fichier ``.prm`` de
la même façon que vous le feriez pour un fichier CSV ou OPE : au lieu de
charger des cibles, il est enregistré dans ``~/.spot/prm`` (et conservé) afin
que les fichiers OPE chargés ultérieurement puissent résoudre les cibles
qu'ils référencent.

Informations de la table
========================
La table des cibles résume les informations sur les cibles. Il y a des
colonnes pour des informations statiques comme le nom de la cible, la RA, la
DEC, ainsi que des informations mises à jour dynamiquement pour l'azimut,
l'altitude, une icône de lever/coucher codée par couleur, l'angle horaire, la
masse d'air, la dispersion atmosphérique, l'angle parallactique et la
séparation lunaire.

Utilisation
===========
Pour « marquer » des cibles, sélectionnez une ou plusieurs cibles dans la
liste et appuyez sur « Tag ». Une coche apparaîtra sur le côté gauche sous la
colonne « Tagged » pour indiquer quelles cibles ont été marquées. Pour
démarquer une cible, sélectionnez une ou plusieurs cibles marquées dans la
liste et appuyez sur « Untag ».

Dans la fenêtre `<wsname>_TGTS`, les cibles seront tracées à la position
correspondant à l'heure définie dans le module SiteSelector. La couleur de la
cible sera d'une teinte proche du magenta si la cible est marquée. Si une
cible est sélectionnée, elle apparaîtra en bleu, et le nom aura un fond blanc
avec une bordure rouge dans la fenêtre `<wsname>_TGTS`. Sinon, la cible sera
colorée selon la couleur qui a été sélectionnée manuellement ou
automatiquement lors du chargement du fichier contenant les cibles.

Le bouton « Select All » sélectionnera toutes les cibles de la table.

Sélectionner des cibles et appuyer sur « Delete » retirera les cibles
sélectionnées de la liste. Si seule une ligne de catégorie est sélectionnée
(mais aucune cible), appuyer sur ce bouton supprimera toutes les cibles de la
catégorie.

Sélectionner une seule cible puis cliquer sur « Browse » ouvrira un menu
d'options permettant de rechercher la cible par coordonnée et de présenter
les résultats dans un navigateur web.

Le menu déroulant à côté de « Plot: » change quelles cibles sont tracées dans
la fenêtre `<wsname>_TGTS`. Sélectionner « All » affichera toutes les cibles,
sélectionner « Uncollapsed » affichera les cibles qui ne sont pas repliées
(masquées) dans la table ainsi que les cibles marquées et sélectionnées,
sélectionner « Tagged+Selected » affichera toutes les cibles qui ont été
marquées ou sont sélectionnées, et sélectionner « Selected » affichera
uniquement les cibles qui sont sélectionnées.

Menu des paramètres
===================
Cliquer sur le bouton « Settings » ouvrira un menu contextuel permettant
d'activer certains paramètres.

* Si vous cochez « Merge Targets », toutes les cibles chargées *après cela*
  seront organisées sous un unique en-tête nommé « Targets », au lieu d'être
  regroupées par nom de fichier.
* « List Unreferenced Targets » est un paramètre qui n'affecte que les
  fichiers OPE. Normalement, le module Targets ignore les cibles qui ne sont
  pas référencées dans les commandes. Cocher ce paramètre affichera toutes
  les cibles, qu'elles soient référencées ou non. Cela peut servir à afficher
  les cibles des fichiers d'inclusion PRM.
* Cocher l'option « Plot solar system objects » tracera le Soleil, la Lune de
  la Terre, les planètes et Pluton dans la fenêtre `<wsname>_TGTS`.

* L'option « Rotate target colors » fera en sorte que chaque fichier chargé
  utilise une couleur différente sélectionnée automatiquement pour les cibles
  (cela ne prendra effet que si « Merge targets » est désactivé).
* « Enable DateTime setting » est une option permettant d'activer le réglage
  d'une date/heure fixe si le fichier CSV comporte une colonne « DateTime ».
  Lorsqu'elle est activée, sélectionner une seule cible dans la table réglera
  la date/heure du module SiteSelector sur cette date et cette heure. Le
  format de cette colonne doit être : YYYY-MM-DD HH:MM:SS <TZ>. Si la chaîne
  du fuseau horaire est omise, UTC est supposé.
