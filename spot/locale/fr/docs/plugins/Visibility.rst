+++++++++++++++
Visibility Plot
+++++++++++++++

Cette fenêtre contient un affichage qui montre l'altitude au fil du temps des
cibles sélectionnées dans votre liste de cibles.

.. note:: Cette fenêtre sera vide si aucune cible n'est sélectionnée.

Régions mises en évidence
=========================

Les régions jaunes en haut et en bas sont les zones d'avertissement. Dans ces
régions, les observations sont difficiles en raison d'une masse d'air élevée
ou d'une élévation très haute. Les lignes verticales rouges en pointillés
sont les heures de coucher et de lever du Soleil au site. La région verticale
orange délimite la durée du crépuscule civil, la région verticale lavande
délimite la durée du crépuscule nautique, et la région verticale bleue
délimite la durée du crépuscule astronomique. La région verte marque l'heure
suivant l'heure actuelle.

Définir la plage du tracé
=========================

Pour changer l'intervalle de temps tracé, appuyez sur le bouton étiqueté
« Time axis: » pour ouvrir un menu déroulant. Trois options sont disponibles :
Night Center, Day Center et Current. « Night Center » centrera l'axe temporel
sur le milieu de la nuit, que l'on peut trouver dans la fenêtre
:doc:`polarsky`. L'axe temporel s'étendra d'un peu avant le coucher du Soleil
à un peu après le lever. « Day Center » centrera l'axe temporel sur le milieu
de la journée, et l'axe temporel s'étendra du lever au coucher du Soleil.
« Current » réglera l'axe temporel pour qu'il s'étende d'environ -2 à +7
heures, et s'ajustera automatiquement au fil du temps.

Sélection des cibles
====================

Le menu déroulant à côté de « Plot: » contrôle quelles cibles sont tracées
sur le tracé de visibilité. Sélectionner « All » affichera toutes les cibles,
sélectionner « Uncollapsed » affichera les cibles qui ne sont pas repliées
(masquées) dans la table des cibles ainsi que les cibles marquées et
sélectionnées, sélectionner « Tagged+Selected » affichera toutes les cibles
qui ont été marquées ou sont sélectionnées, et sélectionner « Selected »
affichera uniquement les cibles qui sont sélectionnées.

Menu des paramètres
===================
Cliquer sur le bouton « Settings » ouvrira un menu contextuel permettant
d'activer certains paramètres.

* Tracer la séparation lunaire. Cocher cette option affichera la séparation
  en degrés à chaque heure le long de chaque ligne de tracé, tant que l'objet
  est au-dessus de l'horizon.
* Tracer l'Az/El polaire. Cocher cette option créera une ligne dans la
  visionneuse « <wsname>_TGTS » qui marque la position de chaque cible durant
  la période sélectionnée pour l'axe temporel (voir ci-dessus), et pour les
  cibles retenues par la sélection de cibles du tracé. Cela vous permet de
  voir plus que la seule position de la cible correspondant à l'heure dans
  SiteSelector.
