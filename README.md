# ᛋ Sowilo Community

[![Tests](https://github.com/sowiloprojectcontact/sowilo-community/actions/workflows/tests.yml/badge.svg)](https://github.com/sowiloprojectcontact/sowilo-community/actions/workflows/tests.yml)
![Plateforme : Linux](https://img.shields.io/badge/plateforme-Linux-7c3aed)
![Python : 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab)

**Préversion Linux · Usage personnel non commercial gratuit · IA facultative**

[Installation](#installation-linux) · [Premiers pas](#découverte-en-cinq-minutes) · [Confidentialité](#confidentialité-et-stockage) · [Signaler un problème](https://github.com/sowiloprojectcontact/sowilo-community/issues) · [Documentation](docs/README.md)

Un espace de travail gratuit pour vos notes, vos tâches et vos documents,
avec un assistant IA facultatif. Première version de développement pour Linux.

**Sowilo automatise, l’humain décide.**

Interface sombre avec panneaux violets et accents néon, construite avec Tkinter.
Aucune police ni ressource graphique distante nécessaire.

## Ce que vous pouvez essayer

- **Accueil** : aperçu des notes et des tâches à faire.
- **Notes** : création, édition, recherche locale, sauvegarde et protection contre
  les modifications concurrentes. Ctrl+S pour enregistrer.
- **Tâches** : ajouter, terminer, réactiver et supprimer avec confirmation.
- **Documents** : lecture locale TXT/Markdown UTF-8, PDF textuels et DOCX.
- **Chat** : conversation avec Groq, reformulation et préparation de brouillons.
- **Résumer, Rechercher, Extraire** : analyse du texte sélectionné, sinon du texte
  de la vue. Confirmation avant chaque analyse IA. Recherche locale sans IA.
- **Résultats réutilisables** : copier, relire et enregistrer une nouvelle note,
  ou confirmer une tâche. Chat utilise la sélection, sinon la dernière réponse.
- **Premiers pas** : guide proposé au premier lancement, facultatif et reprenable
  depuis Aide. La progression est conservée entre les lancements.

Notes, tâches et lecture fonctionnent sans compte ni réseau. Groq est le seul
connecteur opérationnel dans cette V1. La frontière fournisseur est séparée pour
permettre des connecteurs ultérieurs ; OpenAI, Gemini, Claude et Mistral ne sont
pas encore implémentés. Chaque utilisateur crée son compte et utilise sa propre clé Groq ; Sowilo ne
fournit ni ne revend d’accès API. Les éventuels frais et quotas sont ceux du
fournisseur. L’accès reste soumis à l’éligibilité du compte et aux conditions Groq,
y compris ses restrictions de public : voir [connexion Groq](docs/API_GROQ.md).
D’autres connecteurs sont envisagés pour la V2, sans disponibilité annoncée en V1.

## Installation Linux

Prérequis : Python 3.10+ avec Tkinter et venv, une session graphique Linux,
et un accès réseau pendant l’installation des dépendances PDF/Word.
L’environnement de développement a été vérifié sous Python 3.12.

Sur Debian/Ubuntu/Zorin, si les prérequis système manquent :

```sh
sudo apt install python3 python3-venv python3-tk
```

Téléchargez les sources avec **Code → Download ZIP**, puis extrayez l’archive.
Vous pouvez aussi utiliser Git :

```sh
git clone https://github.com/sowiloprojectcontact/sowilo-community.git
cd sowilo-community
```

Depuis le dossier du projet :

```sh
./install.sh
./launch.sh
```

Pour ajouter un raccourci avec la rune Sowilo dans le menu Linux, sans sudo :

```sh
.venv/bin/python scripts/install_desktop.py
# Ou lors de l’installation initiale : ./install.sh --desktop
```

Le raccourci pointe vers le dossier actuel. Conservez-le à cet emplacement après
installation ; le script refuse de remplacer un raccourci existant.

Le lanceur n’installe rien et peut être appelé depuis n’importe quel dossier.
Il utilise `.venv/bin/python` s’il existe, sinon Python système.

```sh
./launch.sh --check    # diagnostic sans fenêtre, réseau, clé ni données utilisateur
./launch.sh --version
```

La V1 est une distribution source avec lanceur, pas un paquet .deb/AppImage.
Ne transférez pas un venv d’une machine à l’autre ; exécutez install.sh sur la
machine cible. Le téléchargement réseau de dépendances reste à valider dans
un environnement neuf avant publication.

Un [test d’installation isolée](docs/TEST_INSTALLATION.md) a réussi dans un venv
neuf avec des paquets du cache local, y compris les 119 tests. Le téléchargement
réseau et l’installation sur un système Linux neuf restent à vérifier.

## Découverte en cinq minutes

1. Lancez Community et suivez **Premiers pas** ; chaque étape peut être passée.
2. Créez une note et une tâche, changez de vue puis retrouvez-les.
3. Ouvrez **Documents → Essayer un exemple**. Les quatre fichiers de `examples/`
   contiennent uniquement des données fictives ; vous pouvez les ouvrir un par un.
4. Pour l’IA, obtenez votre clé depuis votre compte sur https://console.groq.com/keys.
   Dans **Configuration**, saisissez-la, vérifiez le modèle puis choisissez
   **Tester et connecter**. Le test vérifie l’accès au modèle auprès de Groq.
5. Posez une question dans **Chat** ou lancez une action sur le document. Relisez
   la confirmation d’envoi, puis vérifiez la réponse dans la source.

Le modèle par défaut est `openai/gpt-oss-20b` chez **Groq**. Le préfixe du nom du
modèle ne signifie pas une connexion à l’API OpenAI. Vous pouvez saisir un autre
modèle disponible pour votre compte Groq ; une incompatibilité sera signalée.
Les réponses ne déclenchent aucun envoi de mail, commande système ou action métier.

## Confidentialité et stockage

- Configuration : `~/.config/sowilo-community/config.json`.
- Notes et tâches : `~/.local/share/sowilo-community/community.sqlite3`.
- Dossier Documents propre : `~/.local/share/sowilo-community/documents/`.
- Les variables XDG_CONFIG_HOME/XDG_DATA_HOME absolues sont prises en compte.
- Dossiers privés 0700 ; fichiers créés avec umask privé et configuration 0600.
- Aucune configuration, base, clé ou donnée d’un autre projet Sowilo n’est importée.
- Les conversations et clés sont en mémoire ; l’historique Chat disparaît à la
  fermeture. Une nouvelle conversation permet de l’effacer avant fermeture.
- Ouvrir un document n’envoie rien. Son texte extrait reste en mémoire, sans copie
  du fichier. L’autorisation d’un dossier inclut ses sous-dossiers et peut être
  retirée dans Configuration. Les chemins sortant de ces racines sont refusés.
- L’IA reçoit uniquement le texte explicitement approuvé, ou les messages de la
  conversation Chat après consentement pour cette conversation. Aucun accès
  automatique aux notes, tâches, autres documents ou fichiers du PC.
- Un appel déjà transmis au fournisseur ne peut pas être annulé par la fermeture
  de l’application. Les règles de conservation du fournisseur s’appliquent.
- Aucun suivi d’usage ou télémétrie ajouté. Les dépendances sont téléchargées
  pendant install.sh ; Groq n’est contacté que sur action utilisateur.

### Coffre de clés facultatif

Par défaut la clé n’est conservée que pour la session, jamais en JSON. Pour
permettre la mémorisation via Secret Service/KWallet :

```sh
.venv/bin/python -m pip install -r requirements-vault.txt
```

Un coffre système doit être disponible et déverrouillé. Community refuse les
backends plaintext ou composites. Sans coffre sûr, la clé reste en mémoire avec
un message explicite. À la session suivante, **Charger du coffre** est une action
explicite. Le service du coffre est **Sowilo Community**, distinct des autres apps.
**Déconnecter** propose d’effacer la clé en mémoire et, au choix, celle du coffre.
Les clés d’environnement GROQ_API_KEY ne sont pas importées automatiquement.

## Sauvegarder et déplacer

Dans **Configuration → Vos données** :

- **Sauvegarder** produit un JSON privé contenant notes, tâches et leurs dates.
- **Restaurer** valide le fichier (50 Mio maximum), demande une confirmation puis
  remplace les notes/tâches dans une transaction. Une copie des données précédentes
  est enregistrée dans le sous-dossier `backups/` de l’espace de données Community.
  Les identifiants sont renouvelés pour protéger les fenêtres restées sur une ancienne
  sélection. Fermez les autres fenêtres avant la restauration.
- **Exporter les notes** crée un nouveau dossier de fichiers Markdown, sans écraser
  un export précédent.

Ces fichiers ne sont pas chiffrés : conservez-les dans un emplacement de confiance.
Les clés, conversations, autorisations et documents externes ne font pas partie
de la sauvegarde. Aucun fichier document externe n’est modifié par la restauration.
Pour sauvegarder aussi la configuration, copiez séparément son dossier, application
fermée. Le coffre système possède son propre fonctionnement de sauvegarde.

Le projet peut être déplacé ; les données restent dans les chemins XDG.
Une configuration illisible est signalée et conservée, sans réinitialisation silencieuse.

## Limites de cette V1

- Linux seulement validé comme cible ; aucune distribution Windows/macOS annoncée.
- Pas d’OCR, de TTS ou STT. TTS prévu en V2 ; STT à étudier.
- Source Documents : 20 Mio, texte extrait : 200 000 caractères, DOCX décompressé :
  50 Mio. Pour l’IA : 60 000 caractères maximum, sans troncature silencieuse.
- Chat : 16 000 caractères par message et 60 000 caractères / 40 messages dans
  l’historique envoyé. Créez une nouvelle conversation si la limite est atteinte.
- Les documents sont lus en arrière-plan, mais un parseur peut demander du temps.
  Les dossiers autorisés doivent être de confiance ; l’échange malveillant d’un
  répertoire parent pendant la lecture n’est pas complètement empêché.
- Une seule lecture ou requête IA en cours. La navigation reste disponible pendant
  la lecture ou une réponse IA ; Notes et Tâches restent utilisables. Les vérifications
  de connexion gardent leur vue jusqu’à la fin. Une panne réseau conserve le brouillon
  Chat, même après changement d’écran. Le résultat est accessible par « Dernier résultat ».
- Les actions rapides sont masquées dans les vues sans contenu à analyser et désactivées
  sans texte, ou sans clé IA pour Résumer/Extraire. Avant chaque analyse, le périmètre
  sélectionné est nommé explicitement.
- Les champs libres ne sont pas interprétés comme du code ; l’assistant n’a pas
  d’outils d’action. Les réponses IA peuvent être erronées.
- L’utilisateur a confirmé les essais fonctionnels, Groq et la vérification de
  l’interface sur sa machine. Le coffre réel et une installation réseau sur un
  système neuf restent à vérifier avant publication. Voir `docs/TEST_INSTALLATION.md`,
  `docs/VALIDATION.md` et `docs/RECETTE.md`.

## Développement

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q main.py community modules sowilo_data.py sowilo_mini.py tests
.venv/bin/python -m pip check
.venv/bin/python scripts/package.py
```

`community/` contient le shell et l’intégration ; `sowilo_data.py` et
`sowilo_mini.py` reprennent les fonctions locales ; `modules/documents/` contient
la brique de lecture réutilisée. Provenance dans `docs/PROVENANCE.json`.
Le paquet source exclut environnements, données, secrets, caches et archives.
Les [contrôles GitHub Actions](https://github.com/sowiloprojectcontact/sowilo-community/actions/workflows/tests.yml)
vérifient les dépendances, le diagnostic de lancement, les tests et la syntaxe sous
Python 3.12. Ils ne remplacent pas une recette graphique ni un test sur un système
Linux de bureau neuf.

## Publication et licence

Éditeur : Rémy Duhem, entrepreneur individuel. Contact :
[sowiloprojectcontact@gmail.com](mailto:sowiloprojectcontact@gmail.com).

Cette version est une préversion Linux. Les sources ont été envoyées sur
[le dépôt GitHub officiel](https://github.com/sowiloprojectcontact/sowilo-community)
le 26 octobre 2026 ; les deux premières exécutions de la CI ont réussi. Une release publique n’est pas
encore annoncée et l’installation sur Linux neuf reste non validée.
Community est distribuée sous une [licence personnelle propriétaire](LICENSE),
version 1.0, au nom de Rémy Duhem, entrepreneur individuel : usage personnel
non commercial gratuit et modifications privées autorisées ; usage professionnel,
redistribution et revente soumis à une autorisation distincte. Les droits des
composants tiers et les exceptions légales restent préservés. Community n'est
pas un logiciel open source.

Les composants tiers sont recensés dans les [notices tierces](THIRD_PARTY_NOTICES).
Les documents de provenance, de validation et de préparation à la diffusion sont
regroupés dans l’[index de documentation](docs/README.md).

## Aide et retours

Pour signaler un problème, ouvrez une
[issue](https://github.com/sowiloprojectcontact/sowilo-community/issues) en indiquant
votre distribution Linux, la version de Python, les étapes de reproduction et le
message d’erreur. Retirez les clés API et les contenus personnels des captures
et journaux partagés.
