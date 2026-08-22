++++++++
Sky Cams
++++++++

Le module SkyCam sert à placer une image de caméra tout-ciel en arrière-plan
du canal Targets, afin de faciliter la surveillance des conditions du ciel. Un
menu déroulant propose plusieurs sites au choix.

Définir l'image du ciel
=======================

Sélectionnez le serveur de caméra que vous souhaitez utiliser dans le menu
déroulant sous « All Sky Camera ». Cochez ensuite la case en regard de « Show
Sky Image » pour afficher l'image dans la fenêtre `<wsname>_TGTS`. L'image du
ciel peut mettre quelques instants à apparaître. Lorsque l'image se met à
jour, l'heure et la date de la dernière image s'affichent en bas de la
fenêtre, sous « Image Download Info ».

Le module SkyCam peut également générer une image différentielle à partir du
serveur de canal sélectionné en cochant la case en regard de « Show
Differential Image ».

Ajouter de nouvelles caméras
============================

Vous pouvez facilement ajouter vos propres images de caméra tout-ciel si vous
disposez d'un flux d'images approprié pouvant être récupéré via des
protocoles web. Si vous avez récupéré le code source de SPOT, vous trouverez
le fichier « skycams.yml » dans .../spot/spot/config/. Copiez ce fichier dans
$HOME/.spot et modifiez-le pour ajouter votre propre caméra. Vous devrez
fournir une URL de téléchargement des images, un titre, un pixel central
(coordonnées X et Y) dans l'image représentant le zénith, le rayon du cercle
jusqu'à l'horizon en pixels, une rotation à appliquer, s'il faut retourner
l'image dans les dimensions X ou Y, et un intervalle de mise à jour mesuré en
secondes.

Redémarrez spot et vous devriez pouvoir choisir votre nouvelle caméra dans la
liste.
