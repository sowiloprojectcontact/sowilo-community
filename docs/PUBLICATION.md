# État de publication

État vérifié le 26 octobre 2026.

Le dépôt [sowiloprojectcontact/sowilo-community](https://github.com/sowiloprojectcontact/sowilo-community)
est **public**. Les sources sont disponibles sur `main`. Aucune release ni aucun
tag n’est publié à cette date ; Community reste une préversion Linux.

## Vérifications réalisées

- Les deux premières exécutions de GitHub Actions ont réussi, dont celle du
  [commit `1fd56bd`](https://github.com/sowiloprojectcontact/sowilo-community/actions/runs/40293453856).
- Les 119 tests ont également réussi lors de la vérification locale du 26 octobre.
- Le diagnostic `./launch.sh --check` et `pip check` réussissent.
- Une installation dans un venv neuf depuis les paquets du cache a réussi :
  voir [le rapport d’installation](TEST_INSTALLATION.md).
- L’utilisateur a confirmé les essais de l’interface et de Groq sur sa machine.
- Le README, la licence personnelle et les notices tierces sont présents.

La CI installe les dépendances depuis le réseau sur Ubuntu. Elle ne lance pas
`install.sh` et ne valide pas le parcours graphique sur un Linux de bureau neuf.

## Points ouverts pour une release

- [ ] Exécuter `install.sh` avec téléchargement réseau sur une distribution Linux neuve.
- [ ] Vérifier le lancement graphique et les parcours essentiels sur cette installation.
- [ ] Valider le stockage et le chargement d’une clé dans un vrai coffre Secret Service/KWallet.
- [ ] Ajouter des captures d’écran avec uniquement des données fictives.
- [ ] Finaliser les [notes de préversion](NOTES_PREVERSION.md), choisir un tag et
  joindre l’archive source ainsi que sa somme SHA-256 à la release.

## Maintenance du dépôt

La branche `main` n’est pas protégée au moment de la vérification. Une protection
avec contrôle CI requis pourra être configurée pour encadrer les contributions.
Avant chaque envoi, relire les changements et vérifier l’exclusion des clés,
bases, environnements et données personnelles.

## Licence et provenance

La [licence personnelle version 1.0](../LICENSE) autorise l’usage personnel non
commercial gratuit et les modifications privées. Les autres usages sont soumis
aux conditions du texte ; Community n’est pas un logiciel open source.
Les composants tiers conservent leurs propres droits : voir les
[notices tierces](../THIRD_PARTY_NOTICES).

Les audits datés conservent l’historique de préparation. Pour l’état actuel,
utiliser cette page et le README. Les décisions antérieures restent consultables
dans le [contrôle du 26 octobre](CONTROLE_PUBLICATION_2026-10-26.md), la
[revue de licence](REVUE_LICENCE_PERSONNELLE.md) et l’[audit des licences](AUDIT_LICENCES.md).
