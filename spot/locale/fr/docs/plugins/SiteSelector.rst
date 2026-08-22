SiteSelector
============
Le module SiteSelector sert à sélectionner le lieu depuis lequel vous
prévoyez d'observer, ainsi que l'heure d'observation à ce lieu.

Vous voudrez presque toujours démarrer ce module en premier, car il contrôle
de nombreux aspects des autres modules visibles dans l'espace de travail.

Définir le lieu d'observation
-----------------------------
Utilisez le menu déroulant « Site: » pour sélectionner le lieu
d'observation. Plusieurs sites prédéfinis sont disponibles.

Ajouter votre propre lieu d'observation personnalisé
----------------------------------------------------
Si le lieu souhaité n'est pas disponible, vous pouvez facilement ajouter le
vôtre. Si vous avez récupéré le code source de SPOT, vous trouverez le
fichier « sites.yml » dans .../spot/spot/config/. Copiez ce fichier dans
$HOME/.spot et modifiez-le pour ajouter votre propre site. Veillez à définir
toutes les clés de votre site (latitude, longitude, altitude, etc.).
Redémarrez spot et vous devriez pouvoir voir votre nouveau lieu.

Définir l'heure d'observation
-----------------------------
L'heure peut être réglée sur l'heure actuelle ou sur une heure fixe. Pour la
régler sur l'heure actuelle, choisissez « Now » dans le menu déroulant « Time
mode: ».

Pour définir une heure fixe, choisissez « Fixed » : cela activera les
commandes « Date time: » et « UTC offset (min): ». Saisissez la date/heure
dans la première case au format YYYY-MM-DD HH:MM:SS et appuyez sur « Set ».

Par défaut, le décalage UTC de l'heure fixe sera réglé sur celui du fuseau
horaire du lieu d'observation ; mais vous pouvez saisir un décalage
personnalisé (en *minutes*) par rapport à UTC dans l'autre case et appuyer
sur « Set » pour indiquer un décalage spécial d'interprétation de l'heure.

.. note:: cela NE change PAS le fuseau horaire du lieu d'observation ; cela
          règle seulement l'interprétation de l'heure fixe que vous
          définissez.

Mise à jour des modules
-----------------------
Chaque fois que vous changez le lieu d'observation ou l'heure, les autres
modules devraient se mettre à jour automatiquement (s'ils s'abonnent aux
changements de site et d'heure, ce à quoi la plupart sont conçus).

.. important:: Fermer ce module peut empêcher d'autres modules de fonctionner
               comme prévu. SiteSelector est important comme source des mises
               à jour de temps pour presque tous les autres modules, et si
               vous le fermez complètement, son suivi du temps ne déclenchera
               plus les mises à jour de ces autres modules. En cas de doute,
               démarrez et réduisez ce module plutôt que de le fermer.
