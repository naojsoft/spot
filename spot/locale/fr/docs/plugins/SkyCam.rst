++++++++
Sky Cams
++++++++

Le module SkyCam sert à placer une image de caméra tout-ciel en arrière-plan
du canal Targets, afin de faciliter la surveillance des conditions du ciel. Un
menu déroulant propose plusieurs sites au choix.

Définir l'image du ciel
=======================

Le module comporte deux onglets : les commandes décrites ci-dessous se
trouvent dans l'onglet « Caméra », et l'onglet « Historique » affiche la
couverture nuageuse au fil du temps (voir « Historique de la couverture
nuageuse »).

Sélectionnez le serveur de caméra que vous souhaitez utiliser dans le menu
déroulant sous « Caméra tout-ciel ». Cochez ensuite la case à côté de « Afficher l'image du ciel » pour afficher l'image dans la fenêtre `<wsname>_TGTS`. L'image
du ciel peut mettre quelques instants à apparaître. Lorsque l'image est mise
à jour, la date et l'heure de la dernière image s'affichent en bas de la
fenêtre, sous « Infos de téléchargement de l'image ».

Certaines caméras tout-ciel produisent des images en couleur. Cocher la case
« Monochrome » les convertit en image monochrome (niveaux de gris) ;
décochez-la pour afficher les couleurs d'origine.

L'image du ciel est dessinée avec la table de couleurs et les niveaux de
coupure de la visionneuse : vous pouvez donc régler son contraste et ses
niveaux de coupure avec les commandes habituelles de la visionneuse (pour
une image en couleur, seuls les niveaux de coupure s'appliquent). Vos
réglages sont conservés à l'arrivée de nouvelles images.

Image différentielle
====================

Cochez la case à côté de « Afficher l'image différentielle » pour afficher, au lieu
de l'image elle-même, l'évolution du ciel entre les deux dernières images de
la caméra. Les nuages qui se déplacent ou se forment sont ainsi beaucoup
plus faciles à voir. Avec la table de couleurs par défaut « Gris », les
zones inchangées apparaissent en gris moyen, celles devenues plus brillantes
sont plus claires et celles devenues plus sombres sont plus foncées. Les
nuages éclairés par la Lune ou par les lumières des villes deviennent
généralement plus brillants ; les nuages qui masquent les étoiles ou la Voie
lactée deviennent plus sombres.

Pour créer l'image différentielle, les deux images sont converties en
monochrome, leur résolution est réduite et un filtre médian leur est
appliqué, ce qui élimine la plupart des étoiles et du bruit. L'image
précédente est mise à l'échelle de la luminosité globale de l'image
actuelle, afin que les variations d'exposition de la caméra ne ressemblent
pas à des nuages. La différence est ensuite divisée par une estimation du
bruit de l'image : l'image différentielle est donc exprimée en unités de
bruit (« sigma »).

Les commandes sont les suivantes :

* « Compenser la rotation du ciel » : le ciel tourne d'environ un quart de degré par minute,
  si bien que les étoiles se déplacent d'une image à l'autre. Lorsque cette
  case est cochée, l'image précédente est tournée autour du pôle céleste
  jusqu'à l'heure de l'image actuelle, de sorte que les étoiles s'annulent
  et que seuls les changements réels subsistent. Cela suppose que
  l'orientation de la caméra dans skycams.yml soit correcte (voir « Ajouter
  de nouvelles caméras »). Les objets fixes dans le champ de la caméra, tels
  que des coupoles ou des arbres près de l'horizon, peuvent alors laisser
  des traînées courbes.

* « Seuil » : une variation supérieure à ce nombre de sigmas est
  comptée comme nuage pour la couverture nuageuse (5 par défaut).

* « Table de couleurs » : la table de couleurs de l'image différentielle. « Gris »
  et « Variation » (qui n'indique que l'ampleur de la variation, et non si la
  zone est devenue plus brillante ou plus sombre) préservent la lisibilité
  des superpositions de cibles ; « Bleu-vert/Ambre » et « Bleu/Rouge » montrent le
  sens de la variation par la couleur.

* « Couverture nuageuse » : le pourcentage du ciel situé à moins de 75 degrés du
  zénith qui a varié de plus que le seuil. Il mesure les nuages qui se
  déplacent ou changent d'une image à l'autre ; un ciel uniformément couvert
  qui ne change pas n'apparaîtra pas. Tant que le Soleil est à moins de 12
  degrés sous l'horizon au niveau de la caméra, la luminosité du ciel
  change trop vite pour que la valeur ait un sens : « Crépuscule » ou
  « Jour » est alors affiché à la place. La couverture nuageuse est mesurée
  dès que deux images sont disponibles, même si l'image différentielle n'est
  pas affichée.

L'image différentielle conserve sa propre table de couleurs et ses propres
niveaux de coupure (de -10 à +10 sigma par défaut), distincts de ceux de
l'image normale, que vous pouvez également régler avec les commandes
habituelles de la visionneuse.

Après la sélection d'une caméra, l'image différentielle apparaît dès qu'une
deuxième image a été reçue. Si un téléchargement renvoie la même image que
le précédent (la caméra n'a pas encore été mise à jour), il est ignoré.

Le bouton « Enregistrer la configuration » enregistre vos sélections actuelles (serveur de
caméra, « Afficher l'image du ciel », « Afficher l'image différentielle » et « Monochrome »)
pour l'espace de travail, afin qu'elles soient restaurées à sa prochaine
ouverture.

Historique de la couverture nuageuse
====================================

L'onglet « Historique » affiche la couverture nuageuse des 12 dernières
heures, avec les heures dans le fuseau horaire du site sélectionné dans
SPOT. Un point est ajouté pour chaque nouvelle image de la caméra, que
l'image différentielle soit affichée ou non. Les points obtenus au
crépuscule ou de jour sont dessinés creux, et la ligne est interrompue là
où des images manquent. Modifier le seuil ne change que le dernier point.
« Effacer » vide l'historique, qui est aussi effacé quand vous sélectionnez
une autre caméra.

Ajouter de nouvelles caméras
============================

Vous pouvez facilement ajouter vos propres images de caméra tout-ciel si
vous disposez d'un flux d'images adapté pouvant être récupéré par les
protocoles web. Si vous avez récupéré le code source de SPOT, vous trouverez
le fichier « skycams.yml » dans .../spot/spot/config/. Copiez ce fichier
dans $HOME/.spot et modifiez-le pour ajouter votre propre caméra. Vous devrez
fournir une URL de téléchargement des images, un titre, un pixel central
(coordonnées X et Y) de l'image représentant le zénith, le rayon en pixels
du cercle jusqu'à l'horizon, une rotation à appliquer, s'il faut retourner
l'image selon X ou Y, et un intervalle de mise à jour exprimé en secondes.
Vous pouvez aussi indiquer la position de la caméra en degrés sous les clés
« latitude » (négative dans l'hémisphère sud) et « longitude » (négative à
l'ouest de Greenwich). La latitude sert à compenser la rotation du ciel dans
l'image différentielle, et les deux servent à savoir quand il fait nuit au
niveau de la caméra. À défaut, la position du site sélectionné dans SPOT
est utilisée, ce qui est inexact si la caméra se trouve sur un autre site.

Certaines caméras ne publient qu'une image animée (par exemple une boucle
GIF des dernières images). SPOT utilise alors la dernière image de
l'animation, qui est normalement la plus récente ; pour en utiliser une
autre, indiquez son numéro sous la clé « frame » (en comptant à partir de
0, ou de -1 pour la dernière).

La rotation et les retournements doivent orienter l'image de sorte que le
nord soit en haut et l'est à gauche, comme dans le graphique polaire du ciel
(dans les deux hémisphères). Une bonne vérification consiste à s'assurer que
la Lune ou une planète brillante de l'image du ciel coïncide avec sa
position dans SPOT, et que les étoiles s'annulent dans l'image
différentielle lorsque « Compenser la rotation du ciel » est coché.

Redémarrez spot et vous devriez pouvoir choisir votre nouvelle caméra dans
la liste.
