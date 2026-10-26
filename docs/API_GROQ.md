# Connexion facultative à Groq

Vérification du 26 octobre 2026 sur le code local et les sources officielles.

## Fonctionnement de Community

L'utilisateur crée son compte et sa clé directement chez Groq. Il saisit sa clé
dans Community. Les appels partent directement du PC vers
https://api.groq.com/openai/v1 : aucun serveur Sowilo ne sert d'intermédiaire.
Sowilo ne fournit pas de clé commune, ne vend pas d'accès à un compte Groq et
ne facture pas de crédits API. La gratuité de Community ne garantit pas celle
du fournisseur. Les liens vers Groq informent et dirigent vers un service tiers ;
le connecteur effectue de véritables appels si l'utilisateur l'active.

Le test de connexion interroge la liste des modèles ; il ne prouve pas à lui seul
qu'une génération sera acceptée pour le quota et le compte concernés. Le modèle
par défaut openai/gpt-oss-20b est listé par Groq lors de cet examen. Il s'agit d'un
appel à Groq, pas à l'API OpenAI. Les autres connecteurs sont envisagés en V2 ;
aucune compatibilité supplémentaire n'est annoncée pour cette V1.

## Conditions indépendantes

L'utilisateur doit disposer d'un compte éligible, respecter les conditions Groq
et celles du modèle choisi, et être autorisé à envoyer les contenus concernés.
Le [contrat Groq](https://console.groq.com/docs/legal/services-agreement)
consulté affiche une modification au 22 juin 2026. Il prévoit notamment :

- un accès à partir de 18 ans ;
- des services destinés aux développeurs et aux organisations, avec une exclusion
  de l'usage consommateur direct dans son introduction ;
- l'intégration dans des applications clientes et l'accès par des utilisateurs
  finaux sous conditions (article 3.1) ;
- l'interdiction de revendre ou louer l'accès à son compte (article 3.2).

Notre lecture : fournir sa clé personnelle distingue ce parcours d'une revente
d'accès, mais ne prouve pas une éligibilité universelle à Groq. L'articulation
entre usage personnel, compte développeur et application cliente reste à clarifier
auprès de Groq pour le public visé. Aucune autorisation particulière de Groq n'a
été produite pour cet examen. Ni cet avertissement ni le consentement technique
ne remplacent les droits et conditions applicables. Les fonctions locales restent
utilisables indépendamment du service.

Sources complémentaires : [cadre contractuel](https://console.groq.com/docs/legal/contractual-framework-overview),
[politiques applicables](https://console.groq.com/docs/legal),
[usage acceptable](https://console.groq.com/docs/legal/ai-policy),
[modèles](https://console.groq.com/docs/models),
[licence du modèle par défaut](https://huggingface.co/openai/gpt-oss-20b/blob/main/LICENSE).

## Données envoyées et conservation

Community demande un accord avant l'envoi d'une conversation, puis inclut son
historique lors des messages suivants. Pour une analyse de document, l'accord
porte sur la sélection ou le texte affiché. Les autres notes, tâches et fichiers
ne sont pas automatiquement joints. L'ouverture d'un document seule n'envoie rien.

La clé reste en mémoire sauf demande explicite d'un stockage dans un coffre
système accepté. Elle n'est pas écrite dans le JSON. Les conversations ne sont
pas conservées par Community après fermeture. Cela ne décrit pas la conservation
chez Groq : sa [documentation des données](https://console.groq.com/docs/your-data)
prévoit des métadonnées d'usage, et une conservation limitée des entrées/sorties
pour la fiabilité ou la lutte contre les abus, généralement jusqu'à trente jours
sauf obligation légale. Des réglages Zero Data Retention sont proposés au compte.
Les données retenues sont annoncées comme stockées aux États-Unis. Community ne
configure pas ces réglages et ne promet pas une absence de conservation distante.

Les réponses doivent être vérifiées. Aucune réponse ne déclenche de commande
système, d'envoi de mail ou de modification automatique d'un document.
