# Validation de Community V1 — préversion locale

Le contrôle le plus récent, après retrait du catalogue le 25 octobre 2026,
est décrit dans [AUDIT_PREPUBLICATION.md](AUDIT_PREPUBLICATION.md).
Les passages ci-dessous conservent l'historique des validations précédentes.

Contrôles réalisés le 24 octobre 2026, Linux / Python 3.12.

## Résultats vérifiés

- **95 tests réussis**, sans échec ni omission, en 7,057 s.
- Notes/tâches : persistance SQLite, conflits d’édition, migration, rollback,
  suppression contrôlée, recherche locale et préservation des brouillons.
- Documents : vraies lectures TXT/MD/PDF/DOCX temporaires, limites, chemins
  hors autorisation, fichiers spéciaux et diagnostics PDF sans contenu privé.
- IA : réponses et erreurs HTTP simulées, endpoint fixe, redirections refusées,
  limites avant envoi, modèle absent, erreurs sans clé affichée, consentement.
- Chat : historique modifié seulement après succès, refus conservant le brouillon,
  restauration de l’éditeur et séparation des autres données de l’application.
- Configuration : namespace propre, JSON sans secret, permissions 0700/0600,
  coffre simulé distinct, refus des backends non sûrs, aucune clé d’environnement
  importée ni lecture automatique du coffre au démarrage.
- Premiers pas : progression persistante, fin, reprise, redémarrage et rollback
  après échec d’enregistrement.
- Les vrais constructeurs des vues Chat, Documents, Configuration et des quatre
  étapes du guide sont exercés avec widgets simulés. Ce n’est pas un contrôle visuel.
- Travail hors thread Tkinter, application des résultats sur le fil principal,
  navigation protégée pendant une opération et erreurs inattendues masquées.
- Diagnostic `./launch.sh --check` réussi, sans stockage, secret ou appel réseau.
- Code déplacé dans un chemin avec espaces : diagnostic réussi depuis /tmp.
- `pip check` : aucune dépendance cassée dans le venv local préparé.
- Compilation Python et syntaxe bash des lanceurs réussies.
- Les empreintes des dix fichiers source de référence sont inchangées.

Le venv de développement est indépendant : copies de distributions nécessaires
et de leurs métadonnées/licences depuis l’environnement Documents déjà installé.
Aucun pip réseau réussi n’est revendiqué ; aucun lien vers un venv ou une source
métier d’un autre projet. L’archive n’inclut aucun venv.

## Contrôles restant nécessaires

- Session graphique réelle : DISPLAY inaccessible dans cet environnement.
- Installation des dépendances depuis Internet sur une machine propre.
- Réponse réelle de Groq avec clé et modèle disponibles pour l’utilisateur.
- Coffre Secret Service/KWallet réel.
- Recette sur petit écran et sauvegarde/restauration manuelle.
- Licence, droits des ressources et dépôt GitHub à confirmer avant publication.
- Le workflow CI est préparé, pas exécuté sur GitHub.

Aucun appel fournisseur, envoi de message, accès micro/caméra ou lancement d’un
projet métier source n’a été réalisé. Aucune modification du site web n’est incluse.
La V1 n’est pas publiée et ne constitue pas une version finale validée visuellement.

Commandes :

```sh
./launch.sh --check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q main.py community modules sowilo_data.py sowilo_mini.py tests scripts
.venv/bin/python -m pip check
bash -n launch.sh install.sh
.venv/bin/python scripts/package.py
```

## Évolution visuelle violet néon

Thème natif séparé dans community/theme.py : palette noir/violet/blanc, focus et
survol contrastés, rune tracée en plusieurs couches, navigation et accueil remaniés.
Taille initiale ajustée à l’écran, avec minimum 900×680. Aucun traitement IA ou
stockage modifié. Après cette évolution : 95 tests réussis en 7,490 s, diagnostic
imports et compilation réussis. Le rendu graphique réel reste à vérifier.

L’utilisateur a confirmé le fonctionnement local de la première interface avant
ce changement ; il n’a pas encore testé l’IA. Cela ne vaut pas une recette complète.

## Harmonisation Notes, Tâches et Chat

Notes dispose d’un carnet latéral et d’un éditeur dans des panneaux arrondis ;
Tâches d’une zone d’ajout et d’une feuille de route ; Chat d’un historique formaté
par rôle et d’un compositeur séparé. Les méthodes métier de stockage, sauvegarde,
conflits et envoi IA sont conservées. Les panneaux se redimensionnent avec la fenêtre.
95 tests réussis (7,891 s), imports et compilation vérifiés. Construction Notes/Tâches
également exercée avec widgets simulés, restauration de note et brouillon de tâche
conservés. Aucune validation visuelle réelle ni requête Groq revendiquée.

## Optimisations V1 : données, navigation et catalogue

Dernier passage : **120 tests réussis**, zéro échec/erreur/omission, 10,022 s.
Compilation Python, syntaxe Bash, diagnostic des imports et pip check réussis.
Tests complets dans TEST_OUTPUT.txt.

- Sauvegarde JSON privée des notes/tâches et dates, limites 50 Mio et validation
  du contenu avant écriture. Aucun secret, document externe ou conversation.
- Restauration dans une transaction avec copie de sécurité prise sous le même
  verrou d’écriture ; rollback testé après échec d’insertion. Nouveaux identifiants
  pour éviter les écrasements depuis une sélection ancienne. Aucun test sur les
  données réelles de l’utilisateur.
- Export Markdown dans un dossier distinct à chaque export, noms sans traversal,
  fichiers 0600 ; sauvegardes/exports explicitement non chiffrés.
- Actions contextuelles, périmètre nommé avant analyse, résultats repliables et
  rappelables. Copie et création de note/tâche nécessitent une action utilisateur,
  avec relecture/édition avant enregistrement. Pas d’action métier automatique.
- Navigation autorisée pendant lecture et analyse IA. Réponse Chat conservée si
  la vue a changé ; aucun accès aux anciens widgets détruits. Le brouillon reste
  récupérable après erreur. La configuration garde sa vue pendant son propre test.
- Catalogue local Gmail, Calendrier, Devis, Factures & Factur-X. Statut « À venir »
  pour leur intégration dans Community. URL et email officiels non renseignés,
  boutons correspondants désactivés. Aucun contact ou paiement envoyé.
- Raccourci Linux facultatif avec icône rune ; installation testée en XDG temporaire,
  chemins avec espaces/pourcentage et refus d’écrasement. Aucun raccourci installé
  dans le profil réel par ces contrôles.

Une installation pip dans un venv neuf a été tentée depuis PyPI, mais n’a pas
abouti dans l’environnement réseau de la session. L’installation sur une machine
neuve n’est donc pas validée. Les essais utilisateur antérieurs incluent Groq ;
les nouvelles interfaces et le nouveau parcours de restauration restent à essayer
visuellement dans une session graphique accessible.

La boutique, les activations et mises à jour automatiques de modules ne sont pas
implémentées. Le catalogue de cette livraison ne télécharge ni n’exécute de code.
