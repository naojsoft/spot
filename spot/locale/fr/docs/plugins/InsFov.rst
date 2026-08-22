++++++++++++++
Instrument FOV
++++++++++++++

Le module Instrument FOV sert à superposer le champ de vision d'un instrument
sur une image de relevé dans la fenêtre `<wsname>_FIND`.

.. note:: Il est important d'avoir préalablement téléchargé dans la
          visionneuse de recherche (à l'aide du module « FindImage ») une
          image dotée d'un WCS précis pour que ce module fonctionne
          correctement.

Sélectionner l'instrument
=========================

L'instrument peut être sélectionné en appuyant sur le bouton « Choose » sous
« Instrument », puis en naviguant dans le menu jusqu'à trouver l'instrument
souhaité. Une fois l'instrument sélectionné, le nom sera renseigné dans
« Instrument: » et un contour du champ de vision de l'instrument apparaîtra
dans la fenêtre `<wsname>_FIND`.

L'angle de position peut être ajusté, ce qui ajustera l'angle de la
superposition du FOV de l'instrument sur l'image. Si la case « Rotate w/PA »
est cochée, l'image de la visionneuse sera pivotée afin que la superposition
du FOV conserve la même orientation.

La RA et la DEC seront renseignées automatiquement en définissant la position
de déplacement dans la fenêtre `<wsname>_FIND` (par exemple par Maj+clic),
mais peuvent aussi être ajustées manuellement en saisissant les coordonnées.
La RA et la DEC peuvent être spécifiées en valeurs décimales (degrés) ou en
notation sexagésimale.

Pour centrer l'image sur le pointage actuel du télescope, cochez la case en
regard de « Follow telescope » dans l'interface du module ``FindImage``. Cela
vous permettra d'observer un dithering en cours sur une zone du ciel si le
WCS de l'image de recherche est raisonnablement précis.

.. note:: Pour que la fonction « Follow telescope » fonctionne, vous devez
          avoir écrit un module compagnon qui récupère l'état de votre
          télescope, comme décrit dans la documentation du module
          TelescopePosition.
