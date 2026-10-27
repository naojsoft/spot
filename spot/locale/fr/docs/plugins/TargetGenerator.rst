++++++++++++++++
Target Generator
++++++++++++++++

TargetGenerator vous permet de générer dynamiquement une cible de plusieurs
façons. La cible peut ensuite être ajoutée à la table du module « Targets ».

.. note:: Assurez-vous d'avoir également ouvert le module « Targets », car il
          est utilisé conjointement avec ce module.

Générer une cible à partir de l'azimut/élévation
================================================

Saisissez simplement un azimut dans la case « Az : » et une élévation dans la
case « El : ». Cliquez sur « Générer une cible » pour convertir les coordonnées AZ/EL
en coordonnées RA/DEC en utilisant l'heure définie du site. Cela remplira les
cases « AD », « DEC », « Équinoxe » et « Nom » de la section suivante. À
partir de là, vous pouvez ajouter la cible comme décrit dans la section
suivante.

Générer une cible à partir de coordonnées connues
=================================================

Si les coordonnées RA/DEC sont connues, elles peuvent être saisies dans les
cases étiquetées « AD », « DEC », « Équinoxe » et « Nom ». Les valeurs peuvent
être données en notation sexagésimale ou en degrés.

.. note:: La « notation SOSS » peut également être utilisée si vous avez
          installé le paquet « oscript ».

Cliquez sur « Ajouter une cible » pour ajouter la cible. Elle apparaîtra dans la
table des cibles du module « Targets ». Sélectionnez-la là de la manière
habituelle pour la voir dans les tracés « PolarSky » ou « Visibility ».

Rechercher une cible sur un serveur de noms
===========================================

Une cible peut être recherchée via un serveur de noms (NED ou SIMBAD) à
l'aide des commandes de la troisième zone. Sélectionnez simplement votre
serveur de noms dans la liste déroulante étiquetée « Serveur », saisissez un
nom dans la case « Nom » et cliquez sur « Rechercher le nom ». Si l'objet est
trouvé, il remplira les cases étiquetées « AD », « DEC », « Équinoxe » et
« Nom » de la deuxième section. À partir de là, vous pouvez ajouter la cible
en cliquant sur le bouton « Ajouter une cible ».
