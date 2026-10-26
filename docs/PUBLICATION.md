# Préparation de Sowilo Community pour GitHub

État au 25 octobre 2026 : préversion locale, publication distante non réalisée.
Le catalogue et les parcours commerciaux ont été retirés de l'application.
Visibilité choisie par le porteur : **dépôt GitHub privé**.
Le dépôt Git local est initialisé sur `main`, sans commit ni dépôt distant.

## Licence personnelle installée

La [licence personnelle version 1.0](../LICENSE) est installée à la racine.
Titulaire : Rémy Duhem, entrepreneur individuel (auto-entrepreneur).
Le porteur a confirmé le 25 octobre 2026 ses droits sur les éléments repris des
projets Sowilo, hors composants tiers identifiés. Cette confirmation est une
déclaration du porteur, pas une vérification indépendante de la chaîne des droits.

Community autorise gratuitement l'usage personnel non commercial et les
modifications privées. L'utilisation professionnelle, la redistribution et la
revente du code propre à Sowilo nécessitent une autorisation distincte.
Les composants tiers conservent leurs propres droits et les exceptions légales
sont préservées. La future version destinée aux clients aura des conditions distinctes.

Ne pas sélectionner une licence MIT/Apache/GPL dans l'assistant de création GitHub :
ces licences ne correspondent pas aux restrictions retenues. Ne pas présenter
Community comme open source. La [revue du texte](REVUE_LICENCE_PERSONNELLE.md)
conserve les décisions et la confirmation du titulaire.

## Contenu préparé

- Sources et tests autonomes dans ce dossier ; aucun autre projet Sowilo à pousser.
- README avec installation, confidentialité, limites et liens vers les audits.
- Workflow `.github/workflows/tests.yml` préparé ; son exécution sur GitHub
  reste à vérifier après le premier envoi.
- `.gitignore` excluant environnements, bases, secrets usuels et archives générées.
  L'exclusion par nom ne remplace pas la relecture des fichiers à publier.
- Paquet source construit par `scripts/package.py`, avec notices légales et
  somme SHA-256. Il n'inclut pas de runtime Python ni de dépendances installées.
- Audit des modifications dans `AUDIT_PREPUBLICATION.md` et audit juridique
  préparatoire dans `AUDIT_LICENCES.md`.

## Avant la mise en ligne

1. Préciser le compte et le nom du dépôt, puis créer ou utiliser un dépôt **privé**.
2. Compléter les mentions d’éditeur et le moyen de contact pour la diffusion ;
   vérifier les mentions tierces correspondant au livrable final. La licence
   personnelle et la confirmation des droits Sowilo sont déjà enregistrées.
3. Clarifier les conditions Groq pour le public visé (voir l'audit des licences).
4. L’interface a été vérifiée par l’utilisateur. Une installation isolée depuis
   des paquets du cache et ses 119 tests réussissent (voir [TEST_INSTALLATION.md](TEST_INSTALLATION.md)).
   Restent le téléchargement réseau, un système Linux neuf et le coffre système réel.
5. Relire `git status --short` et `git diff --cached` avant le premier commit/envoi.
   Vérifier que `.venv`, les bases et les données personnelles restent exclues.
6. Ajouter le dépôt distant choisi, envoyer la branche et contrôler la CI.
7. Préparer captures et notes de version avant un tag ou une release publique.

Aucun dépôt distant ne doit être déduit d'un nom de dossier. La présence publique
des sources ne remplace pas la licence personnelle : un projet public GitHub
permet aussi des mécanismes de consultation et de fork propres à la plateforme,
dont il faut tenir compte dans les conditions de diffusion.
