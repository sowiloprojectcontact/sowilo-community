# Recette manuelle avant diffusion

À effectuer dans une session graphique Linux. Ces étapes ne sont pas annoncées
comme réalisées par les tests automatisés.

1. Extraire l’archive dans un nouveau dossier avec des espaces dans son nom.
   Exécuter install.sh avec accès réseau, puis launch.sh --check et launch.sh.
2. Vérifier rune, palette, navigation, lisibilité, focus clavier et défilement
   Configuration/Aide sur écran 1366×768 puis 1920×1080.
3. Suivre le guide ; avancer, quitter, relancer. Vérifier reprise de l’étape.
   Choisir Plus tard ; vérifier qu’il reste accessible dans Aide et redémarrable.
4. Sans IA : créer/éditer/sauvegarder une note (Ctrl+S), annuler une navigation
   sur brouillon modifié, enregistrer une copie. Ajouter/terminer/réactiver une
   tâche. Fermer/relancer, vérifier les données. Tester deux fenêtres pour les conflits.
5. Lire les quatre exemples. Ouvrir un fichier externe ; refuser puis accepter
   l’autorisation du dossier. Retirer l’autorisation sans supprimer les fichiers.
6. Tester les erreurs : document manquant, PDF image sans texte, mauvaise clé,
   mauvais modèle, absence réseau. Ne pas mettre de vraie clé dans une capture.
7. Connecter une clé Groq dédiée aux essais. Tester Chat, Ctrl+Entrée, nouvelle
   conversation. Vérifier que le brouillon survit à une erreur réseau.
8. Sélectionner un extrait dans Documents et tester les trois actions ; refuser
   une confirmation puis l’accepter. Vérifier la source et l’absence d’invention.
9. Déconnecter, fermer et relancer : la clé ne doit pas être en JSON. Si le coffre
   est utilisé, tester enregistrement explicite, chargement explicite et effacement.
10. Vérifier une sauvegarde/restauration des données application fermée, puis
    refaire les tests sans les projets Sowilo d’origine accessibles.

Décider ensuite : application(s) livrées, licence, dépôt GitHub, tag, captures et
notes de version. Publier seulement la source sélectionnée par le script package,
jamais le dossier personnel ni les bases des autres projets.

## Nouveaux parcours à essayer

- Dans Configuration : sauvegarder notes/tâches ; exporter les notes ; relire un
  export Markdown. Restaurer uniquement un fichier de test après avoir gardé une
  copie de vos données et fermé les autres fenêtres. Vérifier la copie automatique
  dans le dossier backups et l’absence de modification des clés/documents externes.
- Lancer une réponse Chat, naviguer vers Notes et modifier une note. Revenir dans
  Chat après la réponse ; vérifier la conversation et le brouillon après une erreur.
- Vérifier que les actions rapides disparaissent dans les vues non concernées,
  qu’elles se désactivent sur un texte vide, et que la recherche locale reste
  utilisable sans IA. Avant analyse, vérifier « Sélection » ou « Document entier ».
- Copier une réponse, la relire dans « Créer une note », annuler puis enregistrer.
  Créer une tâche après édition du titre. Vérifier qu’un brouillon de note existant
  reste intact. Replier puis rappeler le dernier résultat après changement de vue.
- Vérifier les sept entrées de navigation : Accueil, Notes, Tâches, Documents,
  Chat, Configuration et Aide. Aucun catalogue ou lien commercial ne doit apparaître.
- Installer le raccourci via scripts/install_desktop.py puis le lancer depuis le
  menu Linux. Vérifier icône, démarrage depuis un autre dossier et diagnostic.
