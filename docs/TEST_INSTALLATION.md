# Test d’installation isolée

Essai du 25 octobre 2026, Linux x86_64 / Python 3.12.3.
L’utilisateur a confirmé avoir vérifié l’interface sur son installation actuelle.
Cette confirmation ne constitue pas une recette graphique sur la copie installée ici.

## Méthode

L’archive source a été vérifiée par SHA-256 puis extraite dans un dossier temporaire
dont le nom contient des espaces. Le script `install.sh --desktop` a été lancé
depuis `/tmp`, avec des chemins XDG propres au test. Aucun environnement Python,
base ou fichier de configuration utilisateur existant n’a été copié.

Python, Tkinter et les bibliothèques système sont ceux de la machine hôte :
il s’agit d’un environnement Python neuf, pas d’un nouveau système Linux.

Le premier essai avec téléchargement réseau a échoué sur la résolution du serveur
de paquets. Cet échec ne prouve pas une indisponibilité des versions demandées.
Il ne valide pas non plus leur téléchargement sur une machine connectée.

Pour poursuivre sans réseau, les wheels déjà présents dans le cache pip ont été
copiés, sans modification, dans un répertoire temporaire de paquets. L’installation
a ensuite utilisé `PIP_NO_INDEX=1` et ce répertoire via `PIP_FIND_LINKS` (URL de
fichier encodée pour les espaces). Aucun paquet n’a été installé globalement et
aucun fichier n’a été copié depuis le venv de développement vers le venv testé.

## Résultats

| Vérification | Résultat |
| --- | --- |
| Extraction et création du venv | Réussies ; `include-system-site-packages = false` |
| Téléchargement depuis le serveur pip | Échec réseau / résolution ; reste à valider |
| `install.sh --desktop` depuis les wheels du cache | Réussi, code retour 0 |
| Dépendances de base résolues | pypdf 6.19.0, python-docx 1.2.0, lxml 6.1.3, typing_extensions 4.16.0 |
| `launch.sh --check` depuis un autre dossier | Réussi |
| `launch.sh --version` | Sowilo Community 1.0.0-dev |
| `pip check` après installation | Aucune incohérence |
| Nouvelle exécution de `install.sh` | Réussie, sans réinstallation forcée du venv |
| Raccourci Linux | Créé uniquement dans le dossier XDG temporaire |
| Installation des dépendances du coffre | Réussie, dont keyring 25.7.0 ; `pip check` réussi |
| Outils de développement | Installés depuis le cache pour exécuter les tests |
| Tests sur la copie extraite, avec son propre Python | 119 réussis, aucune erreur, aucun échec ou omission, 10,590 s |
| Isolation avant exécution des tests | Aucune configuration créée ; seul le raccourci présent dans le dossier XDG de données |

Les versions exactes, y compris les dépendances du coffre, sont consignées dans
`INVENTAIRE_INSTALLATION.json`. L’empreinte de l’archive testée y figure également.
Les journaux sont conservés dans `TEST_INSTALLATION_OUTPUT.txt`. La petite archive
mentionnée à la fin de la suite est une fixture du test de packaging.

## Ce qui reste à vérifier

- L’installation avec téléchargement réseau sur une machine connectée.
- Les prérequis et le lancement sur une distribution Linux neuve.
- La fenêtre de la copie nouvellement installée : cette session n’a pas accès au
  serveur graphique. L’interface de l’installation habituelle a été confirmée par
  l’utilisateur, ce qui est une vérification distincte.
- Le stockage et chargement d’une clé dans un vrai coffre Secret Service/KWallet :
  installer ses dépendances ne valide pas ce parcours. Aucune vraie clé n’a été utilisée.

Conclusion : le parcours d’installation et les 119 tests fonctionnent dans un venv
neuf avec des paquets disponibles localement. La validation Internet et sur un OS
neuf reste ouverte. Aucun changement au code de l’installateur n’a été nécessaire.
