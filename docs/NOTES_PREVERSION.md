# Sowilo Community — préversion Linux

Brouillon de notes pour une future release ; aucune publication n'est effectuée
par ce fichier. La date et le tag seront fixés lors de la publication effective.

Un espace personnel pour les notes, tâches et documents TXT/Markdown/PDF/DOCX.
Les fonctions locales fonctionnent sans compte. La connexion facultative à Groq
utilise le compte et la clé de l'utilisateur, sous réserve de son éligibilité et
des conditions du fournisseur. Les frais et quotas éventuels sont ceux de Groq.
D'autres connecteurs sont envisagés pour la V2.

Distribution source Linux : Python 3.10+, Tkinter, venv et une session graphique
sont requis. Sous Debian/Ubuntu/Mint/Zorin :

```sh
sudo apt install python3 python3-venv python3-tk
./install.sh
./launch.sh
```

Usage personnel non commercial sous licence propriétaire ; modifications privées
permises. Ce projet n'est pas open source. Voir LICENSE et THIRD_PARTY_NOTICES.

Validation : 119 tests locaux réussis et première CI GitHub réussie. L'installation
sur un Linux de bureau neuf et le coffre système réel restent non validés.
L'essai Mint en VM a été interrompu avant la recette de Community. Cette préversion
n'est pas un paquet .deb/AppImage et ne contient pas de runtime Python.

Les conversations restent en mémoire dans l'application. L'IA reçoit uniquement
les contenus approuvés, selon les modalités de docs/API_GROQ.md. Les règles de
conservation du fournisseur s'appliquent ; les réponses nécessitent une vérification.

Éditeur : Rémy Duhem, entrepreneur individuel.
Contact : sowiloprojectcontact@gmail.com.
