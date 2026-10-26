# Audit après retrait du catalogue

Contrôles locaux du 25 octobre 2026, Linux / Python 3.12.3.
Destination retenue : dépôt GitHub privé. Aucun envoi distant réalisé.

Mise à jour postérieure à cet audit : la licence personnelle version 1.0 a été
installée dans `../LICENSE` après confirmation des droits Sowilo par le titulaire.
Voir `REVUE_LICENCE_PERSONNELLE.md`. Le nombre de fichiers de l’archive et les
réserves sur la licence ci-dessous décrivent le paquet au moment de cet audit.

## Modifications contrôlées

- Suppression de `community/catalog.py`, de l'import et de la page Modules & packs.
- Suppression des méthodes de boutique et contact commercial ; maintien du lien
  vers la création de clé Groq, nécessaire à la configuration de l'IA.
- Navigation réduite à sept vues : Accueil, Notes, Tâches, Documents, Chat,
  Configuration et Aide. Test des boutons et de leurs destinations avec widgets simulés.
- Retrait des tests spécifiques au catalogue ; conservation du test du raccourci
  Linux dans `tests/test_desktop.py` et des tests de navigation existants.
- Mise à jour du README et de la recette ; historique des anciennes validations conservé.
- Packaging : inclusion des notices sans extension (LICENSE, COPYING, NOTICE,
  THIRD_PARTY_NOTICES), à la racine si présentes et dans les dossiers autorisés.
  Test en dossier temporaire vérifiant présence des notices et exclusion des
  configurations, secrets usuels, bases, environnement, caches et liens symboliques.
- Préparation Git locale sur `main`, sans ajout à l'index, commit ou dépôt distant.
  `.gitignore` complété pour les caches, fichiers de clés et sauvegardes.
- Ajout du suivi de publication privée et d'un historique de préversion.

## Résultats

| Contrôle | Résultat |
| --- | --- |
| Suite unittest complète | 119 tests réussis, aucune erreur, aucun échec ou test ignoré, 9,759 s |
| `./launch.sh --check` | Réussi, sans ouvrir les données ni appeler l'IA |
| `pip check` | Aucune dépendance installée incohérente |
| Compilation Python | Réussie pour sources, scripts et tests |
| Syntaxe Bash | `launch.sh` et `install.sh` valides |
| Recherche dans les sources et tests | Aucune référence active au catalogue ou à ses anciens gestionnaires |
| Exclusions Git | Environnement, dist, config, credentials, SQLite, .env et backups ignorés |
| Analyse des fichiers candidats Git | Aucun motif de clé Groq/OpenAI/GitHub ou de clé privée détecté ; aucun fichier de base ou clé privée candidat |
| Métadonnées du DOCX d'exemple | Créateur `python-docx`, dernier auteur non renseigné |
| Notices collectées lors de l'audit de licences | 12 notices de paquets vérifiées par SHA-256, plus 5 textes système/référence |
| Archive source reconstruite | 66 fichiers, somme SHA-256 cohérente, notices présentes avec leurs empreintes, aucun ancien module catalogue ou environnement embarqué |
| Diagnostic après extraction | Réussi depuis `/tmp` dans un chemin contenant des espaces, avec le Python du venv local ; aucune donnée/configuration créée |

Le journal complet de la suite est conservé dans `TEST_OUTPUT.txt`. L'analyse des
secrets repose sur des noms et motifs connus, pas sur une garantie d'absence de
toute donnée personnelle. Les tests utilisent des données temporaires et des
réponses IA simulées ; aucune vraie clé ni donnée personnelle n'a été utilisée.
Le diagnostic extrait utilise les dépendances locales : il ne valide pas une
installation réseau neuve. La petite archive signalée à la fin du journal de
tests est une fixture temporaire du test de packaging, pas le livrable réel.

## Points restant ouverts

1. **Recette graphique** : DISPLAY inaccessible, pas de Xvfb disponible. Les tests
   de widgets simulés ne constituent pas une validation du rendu visuel ni une
   capture d'écran. Vérifier le menu sans catalogue via `./launch.sh` sur le poste.
2. **Installation propre et coffre réel** : pas de téléchargement réussi sur
   machine neuve ni de Secret Service/KWallet réel testé dans cette session.
3. **Licence personnelle** : orientation confirmée (usage personnel non commercial,
   modification privée autorisée), texte final et titulaire à établir. Les droits
   des reprises et les conditions Groq restent ceux signalés dans AUDIT_LICENCES.md.
4. **GitHub** : compte et nom du dépôt privé non fournis, aucun connecteur GitHub
   utilisable ni outil `gh` disponible dans cette session. Aucun dépôt distant
   créé, aucune CI distante exécutée, aucune release publiée.

Aucune régression n'a été détectée par les contrôles automatisés exécutés. Cela
ne constitue pas une validation complète de publication : la recette graphique,
l'installation propre et les points de licence restent explicitement ouverts.
