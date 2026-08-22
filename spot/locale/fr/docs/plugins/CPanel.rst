CPanel
======
CPanel est le panneau de contrôle (Control Panel) de l'application SPOT.

Utilisez CPanel pour lancer un nouvel espace de travail ou pour ouvrir des
modules de planification de SPOT dans un espace de travail précis.

Créer un espace de travail
--------------------------
Pour ouvrir un espace de travail, choisissez-en un dans la liste déroulante
modifiable (elle est remplie avec les espaces de travail trouvés dans
``$HOME/.spot/workspaces``) — ou saisissez-y un nouveau nom — puis appuyez
sur le bouton « Open Workspace » à sa droite. Les noms des espaces de travail
doivent être uniques. Si vous laissez la case vide, un espace de travail est
créé avec un nom générique.

Sélectionnez l'onglet de l'espace de travail ouvert afin de voir et
d'utiliser les modules qui y seront ouverts.

Sélectionner un espace de travail pour démarrer un module
---------------------------------------------------------
À l'aide du menu déroulant « Select Workspace », choisissez un espace de
travail ouvert dans lequel vous voulez lancer l'un des modules de
planification de SPOT (notez que l'espace de travail doit d'abord avoir été
ouvert avec « Open Workspace »). Utilisez ensuite les cases à cocher
ci-dessous pour démarrer (cocher) ou arrêter (décocher) un module.

Vous voudrez presque toujours démarrer le module « SiteSelector », car il
contrôle de nombreux aspects des autres modules visibles dans l'espace de
travail.

Astuce : réduire les modules
----------------------------
Parfois, vous voulez démarrer un module pour utiliser certaines de ses
fonctions, mais sans forcément vouloir regarder son interface (les modules
« SiteSelector », « PolarSky » et « SkyCam » en sont de bons exemples). Dans
ces cas, vous pouvez démarrer le module puis cliquer sur le bouton de
réduction de l'interface dans la barre de titre du module pour le réduire et
libérer de la place pour d'autres modules.

.. important:: Fermer certains modules peut empêcher d'autres modules de
               fonctionner comme prévu. Par exemple, le module SiteSelector
               est important comme source des mises à jour de temps pour
               presque tous les autres modules, et si vous le fermez
               complètement, son suivi du temps risque de ne plus déclencher
               les mises à jour de ces autres modules. En cas de doute,
               réduisez un module plutôt que de le fermer.

Enregistrer la disposition de l'espace de travail
-------------------------------------------------
En appuyant sur le bouton « Save <wsname> layout », vous enregistrez la
taille et la position actuelles des fenêtres des modules que vous avez
ouverts dans l'espace de travail donné, ainsi que les modules en cours
d'exécution. La disposition de chaque espace de travail est enregistrée
séparément dans ``$HOME/.spot/workspaces/<wsname>/workspace.json``.

Au prochain démarrage de SPOT, lorsque vous ouvrirez un espace de travail du
même nom, il recréera les fenêtres à leurs tailles et positions enregistrées
et relancera les modules qui étaient en cours d'exécution lors de
l'enregistrement.
