# Contrôle avant diffusion — 26 octobre 2026

Périmètre : préversion source Linux, dépôt
https://github.com/sowiloprojectcontact/sowilo-community.
Éditeur : Rémy Duhem, entrepreneur individuel.
Contact communiqué par le titulaire : sowiloprojectcontact@gmail.com.

Ce relevé est une revue technique et documentaire, pas une certification juridique
ni une garantie d'absence de vulnérabilité. L'objectif de 10 h, heure de Paris,
ne dispense pas de traiter les points ci-dessous. Aucune mise en public ou release
automatique n'est programmée par cette session.

## Résultats acquis

- Commit initial 6548741, 72 fichiers, envoyé par le porteur sur main.
- 119 tests locaux réussis dans cette session ; imports et pip check réussis.
- Première CI GitHub réussie, exécution 40287004824 en 37 s, selon la sortie gh
  transmise par le porteur. Aucun accès distant direct opérationnel ici.
- La licence personnelle 1.0 est présente ; les droits sur les reprises Sowilo
  ont été déclarés par le titulaire le 25 octobre, hors composants tiers.
- Les notices pypdf, python-docx, lxml, typing_extensions et des outils de test
  sont présentes sous docs/licences/. THIRD_PARTY_NOTICES explicite leur périmètre.
- Les versions directes déclarées existent sur PyPI lors de la vérification Web.
  La résolution des dépendances indirectes n'est pas entièrement verrouillée.
- La recherche par motifs a examiné les 70 blobs de l'historique Git et les
  fichiers de l'archive source : aucun motif de clé Groq/OpenAI, jeton GitHub
  ou clé privée reconnu. Aucun venv, base utilisateur, wheel, bibliothèque native
  ou fichier de credentials interdit n'est inclus. Il ne s'agit pas d'une preuve
  exhaustive d'absence de secret ou d'un audit complet des vulnérabilités.
- Le test de packaging a réussi après ajout des notices ; présence de LICENSE,
  THIRD_PARTY_NOTICES et des nouvelles notices vérifiée dans l'archive. Sa somme
  SHA-256 a été contrôlée ; le fichier associé est fourni dans dist/.
- Le client actif utilise HTTPS vers Groq, sans SDK externe, bloque les
  redirections et limite les réponses reçues. Les erreurs publiques ne montrent
  pas la clé. Les tests utilisent des fournisseurs et coffres simulés.
- Chaque utilisateur apporte sa propre clé ; aucun compte API Sowilo partagé
  ni intermédiaire réseau Sowilo n'est implémenté. La clé reste en mémoire ou
  dans un coffre sécurisé explicitement choisi, jamais dans le JSON.
- Les analyses demandent un accord d'envoi ; le Chat demande un accord pour
  sa conversation et son historique. Les autres données ne sont pas jointes
  automatiquement. Aucun outil système ou métier n'est donné au modèle.
- Le SVG est un dessin vectoriel local ; aucun téléchargement de police ou
  ressource distante n'est requis par le thème. Les exemples sont fictifs.

## Licence et diffusion publique

La licence est propriétaire : usage personnel non commercial et modifications
privées permis ; ce n'est pas de l'open source. Les permissions des composants
tiers restent distinctes. La diffusion source n'embarque ni Python, ni wheel,
ni bibliothèque native, ni poids du modèle. Les sujets LGPL/liaison et les
notices de tout futur exécutable autonome devront être réexaminés pour ce livrable.

Un passage en public implique les droits GitHub de consultation et de fork
dans le service, même avec une licence propriétaire. La licence actuelle formule
une interdiction large de redistribution. Une précision concrète est préparée
dans [LICENCE_GITHUB_PROPOSITION.md](LICENCE_GITHUB_PROPOSITION.md) ; elle n'est
pas adoptée à la place du titulaire. Le dépôt a été créé privé selon son choix.

## API Groq

Le modèle openai/gpt-oss-20b est actuellement listé par Groq et sa licence amont
est Apache-2.0. Aucun poids n'est fourni. Les droits d'appel API relèvent du contrat
Groq, indépendamment de cette licence de modèle.

Le contrat prévoit l'intégration dans une application cliente (article 3.1),
mais exclut l'usage consommateur direct dans son introduction et réserve l'accès
aux personnes majeures. La clé personnelle n'est pas une preuve que tout compte
ou usage personnel est éligible. Il faut distinguer un compte développeur
autorisé d'une promesse d'accès grand public universel. Aucune confirmation
spécifique de Groq n'a été obtenue dans cette revue ; l'éligibilité pour le public
visé reste une réserve contractuelle, et non une interdiction certaine de publier
du code de connecteur. Le parcours et ses limites sont dans [API_GROQ.md](API_GROQ.md).

Groq annonce des métadonnées d'usage et une rétention possible des entrées/sorties
pour fiabilité ou abus ; des contrôles de rétention sont proposés au compte.
Ne pas annoncer « aucune conservation par Groq », ni un service forcément gratuit.
Les autres modèles et les futurs connecteurs V2 exigent leur propre revue.

## Limites de validation à conserver dans l'annonce

- L'essai Mint en VM a été arrêté à cause du démarrage et des ralentissements.
  Il n'a validé ni l'installation ni l'interface de Community sur Linux neuf.
- Une installation isolée depuis le cache avait réussi le 25 octobre ; un
  téléchargement pip depuis Internet n'a pas été validé dans cette session.
  La CI a installé ses dépendances en ligne, ce qui est une preuve distincte du
  parcours install.sh sur une distribution de bureau neuve.
- Le porteur avait confirmé ses essais graphiques et Groq sur sa machine.
  Aucun nouvel essai graphique réel n'a été réalisé par l'agent ici.
- Coffre réel Secret Service/KWallet non validé ; sa présence simulée ou celle
  de ses paquets ne vaut pas une recette du stockage d'une vraie clé.
- La revue de secrets par motifs et de fichiers exclus réduit les risques sans
  prouver l'absence de tout secret. Les documents historiques d'audit restent
  dans la livraison ; leurs anciens états ne remplacent pas ce relevé.
- Les mentions d'identité et de contact sont celles transmises par le titulaire.
  La conformité exhaustive des obligations d'éditeur pour son mode de diffusion
  n'est pas attestée et aucune donnée administrative n'a été inventée.

La diffusion envisageable doit être présentée comme une préversion Linux en
source, pas comme une version stable entièrement validée sur machine neuve.

## Sources officielles consultées le 26 octobre

- [Conditions GitHub, D.5](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#5-license-grant-to-other-users).
- [Groq Services Agreement](https://console.groq.com/docs/legal/services-agreement),
  introduction, articles 2, 3.1 et 3.2 ; modification affichée au 22 juin 2026.
- [Données Groq](https://console.groq.com/docs/your-data),
  [politiques](https://console.groq.com/docs/legal),
  [usage acceptable](https://console.groq.com/docs/legal/ai-policy).
- [Modèles Groq](https://console.groq.com/docs/models) et
  [licence gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b/blob/main/LICENSE).
- [pypdf 6.19.0](https://pypi.org/pypi/pypdf/6.19.0/json),
  [python-docx 1.2.0](https://pypi.org/pypi/python-docx/1.2.0/json),
  [lxml](https://lxml.de/index.html#license),
  [keyring 25.7.0](https://pypi.org/pypi/keyring/25.7.0/json),
  [typing_extensions 4.16.0](https://pypi.org/project/typing-extensions/4.16.0/),
  [ReportLab 5.0.1](https://pypi.org/project/reportlab/5.0.1/),
  [Pillow 12.3.0](https://pypi.org/project/pillow/12.3.0/).
