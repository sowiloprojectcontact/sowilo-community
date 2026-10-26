# Audit des licences de Sowilo Community V1

Examen du 25 octobre 2026. Périmètre : sources locales, dépendances déclarées,
environnement Python local, archive existante et sources officielles citées.
Ce document prépare le choix de licence ; il ne constitue pas un avis juridique
ni une attestation que tous les droits sont acquis. Aucune licence n'est attribuée
à Sowilo par cet audit.

Mise à jour de périmètre : le catalogue décrit dans l'état initial a été retiré
le 25 octobre 2026. Le packaging conserve désormais les notices sans extension.
Le choix visé est une licence personnelle non commerciale avec modification
privée autorisée, décrite dans `PUBLICATION.md`. Les observations ci-dessous
sur l'ancienne archive et son packaging restent des constats historiques.

Mise à jour de finalisation : le titulaire a confirmé ses droits sur les éléments
Sowilo repris, hors composants tiers, le 25 octobre 2026. La licence personnelle
version 1.0 est maintenant installée dans `../LICENSE`. Cette déclaration est
consignée dans `REVUE_LICENCE_PERSONNELLE.md`. Les réserves techniques sur les
composants tiers et l’API Groq restent ouvertes. Le présent audit initial et ses
formulations antérieures à la finalisation sont conservés comme historique.

## Conclusion pour le choix de licence

Les licences principales des bibliothèques utilisées permettent une application
commerciale, gratuite ou payante, et n'imposent pas à elles seules de publier le
code propre à Sowilo. Une licence propriétaire gratuite, MIT, Apache-2.0 ou GPLv3
reste donc envisageable, sous réserve des droits sur les sources Sowilo et des
conditions propres aux composants réellement redistribués. Gratuit et open source
désignent des choix différents.

La publication n'est pas encore juridiquement validée. Trois réserves demeurent :

1. Les titulaires des droits sur le code repris et les ressources Sowilo ne sont
   pas établis par les fichiers disponibles.
2. Le coffre facultatif n'est pas installé : sa chaîne exacte de versions et ses
   notices ne peuvent pas être attestées sur cet environnement.
3. Une distribution avec interpréteur ou bibliothèques embarqués doit faire
   l'objet d'un inventaire du binaire livré, notamment pour la LGPL et les notices
   secondaires des wheels. L'archive source actuelle ne contient pas ces binaires.

## Ce qui a été vérifié

- `requirements.txt` : pypdf 6.19.0 et python-docx 1.2.0.
- `requirements-vault.txt` : dépendances précédentes et keyring 25.7.0.
- `requirements-dev.txt` : dépendances précédentes, ReportLab 5.0.1 et Pillow 12.3.0.
- Imports dans `main.py`, `community/`, `modules/`, `sowilo_data.py` et
  `sowilo_mini.py`, y compris imports à l'intérieur des fonctions.
- Métadonnées et fichiers de licence des huit paquets installés dans `.venv`.
- `install.sh`, `launch.sh`, `scripts/package.py`, workflow GitHub, SVG et exemples.
- Archive `dist/sowilo-community-1.0.0-preview.tar.gz` existante : 44 entrées,
  sans `.venv`, `site-packages` ou fichier de licence tiers. Cette archive
  précède l'audit ; elle n'a pas été reconstruite.
- `docs/PROVENANCE.json` et recherche des fichiers LICENSE/COPYING dans les
  sources des trois projets Sowilo concernés, hors environnements et sorties générées.

Les copies exactes de notices locales sont dans `docs/licences/`. Le fichier
`INVENTAIRE_LICENCES.json` donne les versions, les dépendances déclarées et les
empreintes SHA-256 des notices de paquets collectées. Les copies de copyright
du système incluent parfois des clauses de packaging ou d'outillage qui ne
s'appliquent pas au seul composant exécuté : lire leurs sections `Files`.

## Bibliothèques de l'application

| Composant | Version constatée | Licence et droits | Obligations en cas de redistribution |
| --- | --- | --- | --- |
| pypdf | 6.19.0 | BSD-3-Clause ; usage, modification, distribution et exploitation commerciale permis | Conserver copyright, conditions et exclusion de garantie ; les reproduire dans les documents accompagnant les binaires ; aucune promotion suggérant l'approbation des auteurs sans autorisation |
| python-docx | 1.2.0 | MIT ; usage commercial, modification, distribution et sous-licence permis | Conserver copyright et permission avec les copies ou parties substantielles |
| lxml, via python-docx | 6.1.3 | BSD-3-Clause pour le cœur, avec autres licences détaillées ci-dessous | Conserver les notices et traiter les bibliothèques ou ressources embarquées séparément |
| typing_extensions, via python-docx ; également pypdf sous Python < 3.11 | 4.16.0 ici | PSF-2.0, avec historique inclus dans la notice | Conserver la licence et les copyrights ; documenter les modifications au composant s'il est modifié et distribué |

Preuves prioritaires : notices de ces versions dans `docs/licences/`. Confirmation
publique pour [pypdf](https://pypi.org/project/pypdf/6.19.0/) et
[python-docx](https://pypi.org/project/python-docx/1.2.0/).
Les dépendances indirectes ne sont pas verrouillées par les requirements actuels :
une nouvelle installation peut obtenir d'autres versions.

### lxml : ne pas se limiter à l'étiquette BSD

Le fichier local `lxml-6.1.3.dist-info/licenses/LICENSES.txt` signale :

- des éléments issus d'ElementTree/cElementTree, et de CPython sous licence PSF ;
- des ressources Schematron avec leurs propres notices ; certaines transformations
  sont décrites comme sans licence dans cette notice. Elles ne sont pas utilisées
  par le lecteur DOCX de Sowilo. Une redistribution intégrale de lxml doit néanmoins
  examiner les fichiers réellement inclus ; leur inutilisation ne supprime pas
  leurs conditions de redistribution ;
- un ancien lanceur de tests GPL, distinct du cœur. La notice présente sa présence
  inchangée pour les tests comme une agrégation, et non comme une mise de lxml sous GPL ;
- des bibliothèques intégrées aux wheels officiels : zlib (licence zlib), libxml2,
  libxslt et libexslt (MIT avec notices particulières), et iconv (LGPL-2.1).

Localement, lxml annonce libxml2 2.14.6 et libxslt 1.1.43 ; `ldd` sur son extension
ne liste que des bibliothèques système usuelles. Cela n'exclut pas des composants
liés statiquement, et ne prouve pas qu'iconv est inclus dans ce wheel précis.

Si libiconv LGPL est redistribué, conserver sa licence et ses notices, fournir
les sources correspondantes et respecter les modalités de liaison/remplacement
ou de réédition des liens applicables. La licence propre à Sowilo doit préserver
les droits de modification et de débogage requis pour cette bibliothèque. La
LGPL ne signifie pas automatiquement que tout Sowilo doit devenir GPL.
Les modalités exactes dépendent du paquet livré : elles restent à contrôler avant
une AppImage, un exécutable autonome ou un bundle hors ligne.

Références : [licence lxml](https://lxml.de/index.html#license), notice locale complète
et texte LGPL-2.1 conservé dans `docs/licences/LGPL-2.1.txt`.

## Coffre facultatif : licences vérifiées en amont, versions finales à inventorier

keyring n'est pas présent dans `.venv`. L'installation du coffre n'a pas été
effectuée pendant cet audit. Les lignes suivantes décrivent la chaîne attendue,
pas un relevé certifié de paquets installés.

| Composant | Rôle / condition | Licence annoncée par la source officielle | Conséquence |
| --- | --- | --- | --- |
| keyring 25.7.0 | API de coffre facultative | MIT | Préserver la notice à la redistribution |
| SecretStorage | Backend Secret Service, Linux | BSD-3-Clause | Préserver copyright, conditions et garantie ; pas d'approbation implicite |
| jeepney | Communication D-Bus, Linux | MIT | Préserver la notice |
| jaraco.classes | Dépendance de keyring | MIT | Préserver la notice |
| jaraco.functools | Dépendance de keyring | MIT | Préserver la notice |
| jaraco.context | Dépendance de keyring | MIT | Préserver la notice |
| more-itertools | Via utilitaires jaraco | MIT | Préserver la notice |
| cryptography | Via SecretStorage | Apache-2.0 OU BSD-3-Clause | Choisir une voie autorisée pour le composant ; conserver aussi les notices des éléments embarqués |
| cffi | Selon version de cryptography et plateforme | Version actuellement publiée : MIT-0 ; anciennes versions à vérifier sur leur notice | Ne pas appliquer cette étiquette à une version non relevée ; contrôler également libffi embarquée, généralement MIT |
| pycparser | Selon version de cffi | BSD | Lire la notice exacte de la version résolue pour les conditions et éventuels éléments repris |
| importlib_metadata | keyring sous Python < 3.12 | Apache-2.0 | Conserver licence, attributions et NOTICE si fourni ; signaler les modifications |
| zipp | Via importlib_metadata selon version | MIT | Préserver la notice |
| backports.tarfile | Via jaraco.context sous Python < 3.12 | MIT annoncé ; code dérivé de CPython à contrôler dans la distribution | Préserver également les notices héritées présentes dans le paquet |

Sources : [configuration exacte de keyring 25.7.0](https://raw.githubusercontent.com/jaraco/keyring/v25.7.0/pyproject.toml),
[SecretStorage](https://pypi.org/project/SecretStorage/),
[jeepney](https://pypi.org/project/jeepney/),
[jaraco.classes](https://pypi.org/project/jaraco.classes/),
[jaraco.functools](https://pypi.org/project/jaraco.functools/),
[jaraco.context](https://pypi.org/project/jaraco.context/),
[more-itertools](https://pypi.org/project/more-itertools/),
[cryptography](https://pypi.org/project/cryptography/),
[cffi](https://pypi.org/project/cffi/), [pycparser](https://pypi.org/project/pycparser/),
[importlib_metadata](https://pypi.org/project/importlib-metadata/),
[zipp](https://pypi.org/project/zipp/) et
[backports.tarfile](https://pypi.org/project/backports.tarfile/).

Les wheels cryptography peuvent embarquer OpenSSL et des composants Rust : leur
inventaire propre est nécessaire si ces wheels sont livrés. Une seule mention
« cryptography BSD » ne couvre pas tout leur contenu.

Le backend KWallet peut nécessiter dbus-python, non déclaré ici dans les requirements.
Les démons GNOME Keyring/KWallet/KeePassXC et D-Bus sont des services système séparés,
non livrés par l'archive source. Leur présence sur le PC n'impose pas leur licence
à Sowilo. Si un futur installateur les redistribue, relever les versions et notices
du choix effectivement livré. Les dépendances Windows/macOS sont hors cible V1 ;
ne pas extrapoler cet audit à un portage.

## Outils de développement et d'installation

| Composant local | Licence | Portée |
| --- | --- | --- |
| ReportLab 5.0.1 | BSD à trois clauses, texte local faisant foi | Déclaré en développement, absent des imports d'exécution de Community |
| Pillow 12.3.0 | MIT-CMU, plus notices des bibliothèques embarquées | Développement ; ne pas réduire son fichier LICENSE à une licence MIT ordinaire |
| charset-normalizer 3.5.2 | MIT | Dépendance de ReportLab |
| pip 24.0 | MIT pour pip ; composants intégrés à contrôler si redistribués | Installation ; absent du paquet source Sowilo |

ReportLab contient aussi DarkGarden, police GPL-2.0-ou-ultérieure avec exception
pour les documents qui l'embarquent, et Bitstream Vera avec licence de police
spécifique. Leur présence dans l'environnement de développement ne place pas
automatiquement Sowilo sous GPL. Un bundle contenant ces polices doit conserver
leurs textes et respecter leurs obligations, dont les sources applicables à la GPL.
Le PDF d'exemple livré utilise `/Helvetica` sans FontDescriptor ; aucune police
DarkGarden/Vera n'y a été trouvée. Le DOCX d'exemple contient une table de noms de
polices, aucun fichier de police incorporée.

Le LICENSE complet de Pillow est conservé. Ses sections concernent AOM, Brotli,
bzip2, dav1d, FreeType2, HarfBuzz, LCMS2, libavif, libjpeg, liblzma, libpng, libtiff,
libwebp, libyuv, OpenJPEG, Raqm, Tcl/Tk, Xau, XCB, XDMCP, zlib et zstd. Les notices
incluent des conditions d'attribution, de conservation et parfois de marquage
des versions modifiées ; FreeType propose notamment la FTL ou la GPL, et la
FTL impose des crédits. La section liblzma distingue la bibliothèque des outils
et scripts de construction sous d'autres licences. La liste des notices n'est
pas une preuve que chaque composant est actif dans chaque wheel. Pour la V1
source, Pillow n'est pas redistribué et aucun de ces éléments n'est embarqué par
Sowilo ; leur conformité binaire n'est donc pas certifiée par cet audit.

Le workflow utilise actions/checkout@v4 et actions/setup-python@v5 : outils CI,
non inclus dans l'application. Aucun outil de compilation n'est automatiquement
une dépendance juridique du résultat ; examiner ce qui est effectivement copié.

## Python, interface, système et ressources graphiques

| Élément | Constat et licence | Obligation / effet sur Sowilo |
| --- | --- | --- |
| CPython / bibliothèque standard | Python 3.12.3 local ; PSF-2.0 et licences historiques/secondaires | Autorise exploitation commerciale ; conserver les textes si Python est embarqué, et les modifications du composant si applicable |
| Tkinter | Module Python utilisant Tcl/Tk | Conserver les notices Python et celles de Tcl/Tk en cas de bundle |
| Tcl/Tk | Série 8.6 locale ; licence permissive Tcl/Tk | Usage, copie, modification et distribution permis ; conserver copyright et texte de licence |
| SQLite | 3.45.1 local ; domaine public déclaré par les auteurs | Usage commercial et distribution permis ; distinguer bibliothèque et scripts de construction |
| OpenSSL | 3.0.13 local utilisé par Python pour HTTPS ; Apache-2.0 | Si embarqué : licence, attributions, NOTICE si fourni et modifications à documenter |
| DejaVu Sans | Police système nommée dans `community/theme.py`, aucun TTF livré | Licence dérivée Bitstream Vera, modifications DejaVu dans le domaine public ; clauses Arev selon glyphes. Si fournie : conserver les notices, restrictions de noms après modification et de vente de la police seule |
| Bash, glibc, X11 et bibliothèques système | Prérequis externes, non inclus dans le paquet source | Leur simple utilisation ne permet pas de déduire une obligation GPL pour les sources Sowilo ; réexaminer un futur runtime embarqué |
| Rune de l'interface et `assets/sowilo.svg` | Dessins vectoriels dans les sources ; pas d'image distante ou de police incluse dans le SVG | Origine et titulaire du dessin à confirmer ; aucune autorisation tierce démontrée par le seul fichier |

Sources : [Python](https://docs.python.org/3/license.html),
[Tcl/Tk](https://www.tcl-lang.org/software/tcltk/license.html),
[SQLite](https://www.sqlite.org/copyright.html),
[OpenSSL](https://openssl-library.org/source/license/index.html),
[DejaVu](https://github.com/dejavu-fonts/dejavu-fonts/blob/master/LICENSE).
Les notices système locales ont été conservées pour Python, Tcl, OpenSSL et DejaVu.
Les autres bibliothèques du système ne font pas l'objet d'un audit complet de
distribution Linux : Sowilo ne redistribue pas le système.

## Groq et modèle IA : contrat distinct

Le client actif `community/groq.py` utilise `urllib`, sans SDK Groq ou OpenAI
installé. Le service Documents réutilisé conserve un import conditionnel
`from openai import OpenAI` dans son ancienne méthode `_analyze`. L'interface
Community emploie la lecture Documents puis `community/ai.py` pour ses analyses :
ce SDK n'est donc pas une dépendance du parcours actuel. Si cette ancienne API
est exposée ou réactivée, ajouter le SDK et auditer ses dépendances réelles.

Le modèle par défaut `openai/gpt-oss-20b` porte la licence Apache-2.0 sur le dépôt
officiel du modèle. Aucun poids n'est livré par Community. L'appel API ne transforme
pas Sowilo en logiciel Apache-2.0. Si des poids sont distribués ultérieurement,
examiner alors licence, NOTICE et politiques associées à cette version.
Source : [licence officielle du modèle](https://huggingface.co/openai/gpt-oss-20b/blob/main/LICENSE).

Le contrat pertinent pour l'API est le
[Groq Services Agreement](https://console.groq.com/docs/legal/services-agreement),
version affichée du 22 juin 2026, et les politiques et conditions de modèles
associées depuis [les mentions légales Groq](https://console.groq.com/docs/legal).
Les conditions générales du site Web ne suffisent pas à établir les droits API.

Points ayant un effet sur le projet : le contrat vise les développeurs et entreprises
et exclut l'usage consommateur de ces services ; il encadre l'intégration dans des
applications clientes, les comptes et les utilisateurs autorisés, interdit certaines
reventes et exige le respect des conditions des modèles. Il impose aussi les avis
et consentements nécessaires au traitement des données. **La destination grand
public de l'option Groq doit être clarifiée au regard du contrat applicable au compte.**
La saisie d'une clé personnelle ne résout pas automatiquement cette question.
Ne pas promettre une API librement revendable ou un accès universel et gratuit à l'IA.
Ces clauses contractuelles n'imposent pas une licence open source à Sowilo.

Un utilisateur peut choisir un autre modèle : sa licence et ses politiques doivent
être examinées à ce moment-là. Cet audit ne valide pas tous les modèles Groq.
Les intégrations Gmail, calendrier, devis et factures affichées « À venir » ne sont
pas des dépendances opérationnelles de cette V1.

## Code repris des autres projets Sowilo : droits à établir

`docs/PROVENANCE.json` enregistre dix reprises et des empreintes de fichiers :

| Origine | Éléments repris |
| --- | --- |
| codex-test | `sowilo_data.py`, `sowilo_mini.py`, tests associés |
| Sowilo-Documents-V1 | Configuration, chemins, service Documents, initialisation du module et tests |
| Sowilo-Builder-0.1 | Client Groq |

Aucun fichier LICENSE/COPYING propre à ces sources n'a été trouvé dans le périmètre
recherché. Cela ne démontre ni que les reprises sont interdites, ni qu'elles sont
libres de droits. Un nom de dossier, un hash ou la présence du code sur ce PC ne
constitue pas une autorisation de relicencier.

Avant de choisir la licence, établir pour les sources, tests, textes, exemples et
dessins : auteur/titulaire, éventuel employeur ou contrat de cession, contributions
externes et code copié. Si tout appartient au même titulaire, conserver une
déclaration de cette origine ; sinon obtenir les autorisations compatibles.
Les fichiers d'exemple sont décrits comme fictifs ; cette description n'est pas
une preuve de titularité des droits. Les éléments produits avec une IA doivent
être rattachés au compte et aux conditions de l'outil utilisé à leur création,
et les reprises tierces éventuelles restent à vérifier.

## Conséquences des choix possibles

| Choix pour le code propre à Sowilo | Droits donnés aux utilisateurs | Limite importante |
| --- | --- | --- |
| Licence propriétaire, utilisation gratuite | Droits définis par un contrat spécifique ; redistribution et modification peuvent être encadrées | Préserver les droits déjà accordés par les licences tierces ; le code livré en clair n'est pas automatiquement open source |
| MIT | Usage, modification, redistribution, sous-licence et vente, y compris forks propriétaires, avec conservation de notice | Ne permet pas d'interdire la revente ou la réutilisation commerciale autorisée |
| Apache-2.0 | Droits permissifs avec licence de brevets, notices et conditions propres | Plus de formalités que MIT ; pas de droit automatique sur les marques |
| GPLv3 | Utilisation commerciale autorisée ; obligations de source et de licence pour les versions dérivées distribuées selon son périmètre | Ne permet pas de réserver l'exploitation commerciale à Sowilo ; compatibilité du paquet final à vérifier |

Cette comparaison est une orientation, pas une sélection automatique. Une clause
« usage commercial interdit » ou « revente interdite » exclurait une licence MIT
ou Apache-2.0 standard et ne constituerait pas une licence open source standard.
Les marques, la garantie, l'assistance et les conditions d'API sont à traiter
distinctement. Les exclusions de garantie des dépendances ne dispensent pas
l'éditeur de ses propres obligations légales impératives.

Textes de référence : [MIT](https://opensource.org/license/mit),
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) ; pour la GPLv3, le texte
est également disponible localement dans `/usr/share/common-licenses/GPL-3`.

## Travail restant avant publication

1. Établir la titularité des éléments Sowilo repris et des ressources, puis choisir
   les droits que l'éditeur souhaite accorder. Ne pas ajouter un LICENSE sans ce choix.
2. Fixer le format de livraison : sources avec téléchargement des dépendances,
   ou paquet autonome. Le paquet source actuel n'embarque aucun runtime tiers.
3. Résoudre dans un environnement isolé les dépendances obligatoires et le coffre
   facultatif sur chaque version Python supportée ; conserver versions, hashes,
   licences exactes et dépendances conditionnelles. Les wheels du coffre ne sont
   pas encore disponibles ici ; le réseau du terminal ne permettait pas leur
   téléchargement lors de l'audit, la vérification Web a servi pour les sources amont.
4. Constituer les mentions tierces du contenu réellement livré. Les copies de cet
   audit sont des preuves de travail, pas une déclaration de conformité du bundle.
5. Pour un bundle, vérifier lxml/libiconv, les ressources Schematron, les composants
   cryptography/OpenSSL/Rust, les polices et les autres bibliothèques natives ;
   fournir notices, sources et possibilités de reliaison requises selon les cas.
6. Clarifier le public autorisé pour Groq et documenter les conditions de l'option IA.
7. Intégrer les textes définitifs au paquet. `scripts/package.py` utilise une liste
   explicite pour les fichiers racine : un futur `LICENSE` ou `THIRD_PARTY_NOTICES`
   racine n'y serait pas ajouté automatiquement. Les preuves actuelles sous `docs/`
   avec extensions `.txt`, `.md` ou `.json` passent sa liste de suffixes ; les copies
   nommées simplement `LICENSE` n'y passeraient pas. Adapter le packaging lorsque
   les mentions de publication seront décidées, et contrôler l'archive finale.

L'audit a uniquement ajouté de la documentation et des preuves de licences. Il
n'a changé ni le comportement de l'application, ni ses dépendances, ni les données
utilisateur, ni la licence du projet.
