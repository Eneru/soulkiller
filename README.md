# Soulkiller

Soulkiller est un projet d'application en plusieurs stages, inspiré du Soulkiller
de Cyberpunk 2077. Le premier objectif est de définir les usages et de construire
progressivement une application faisant appel à des LLM. Les stages, les données
et les comportements attendus restent à spécifier : aucune capacité de
« numérisation de conscience » n'est aujourd'hui implémentée ou démontrée.

## État du projet

Cette initialisation fournit un environnement de développement et des règles de
contribution. Il n'y a encore ni code applicatif, ni serveur, ni suite de tests
fonctionnels. Python, .NET et éventuellement Angular sont des pistes ; leur usage
et leurs versions seront décidés dans les prochaines spécifications.

Le dépôt de référence est [Eneru/soulkiller](https://github.com/Eneru/soulkiller).
Toute évolution passe par une branche et une PR relue par le mainteneur.

## Démarrer dans le devcontainer

Prérequis sur l'hôte :

- Docker avec des conteneurs Linux ; sous Windows, Docker Desktop et son
  intégration WSL 2 activée pour Ubuntu.
- Un éditeur compatible Dev Containers, par exemple VS Code avec l'extension
  Dev Containers.
- Un accès réseau aux registres Ubuntu, Node.js et npm pour la première construction.

Ouvrir le dossier Soulkiller dans l'éditeur puis choisir **Dev Containers: Reopen
in Container**. Le dossier est monté dans `/workspaces/soulkiller` ; le terminal
s'ouvre sous l'utilisateur non-root `ubuntu`. Le démarrage ne lance aucun service
applicatif, appel LLM ou génération de fichiers dans le dépôt.

Pour construire et lancer directement le même environnement depuis un terminal
**hôte ouvert dans Soulkiller**, les seules commandes hôte nécessaires sont :

```sh
docker build -t soulkiller-dev .devcontainer
docker run --rm -it --init --mount "type=bind,source=${PWD},target=/workspaces/soulkiller" soulkiller-dev bash
```

Ces exemples utilisent un shell POSIX, notamment Ubuntu sous WSL. Toutes les
commandes de développement, y compris Git et OpenSpec, s'exécutent ensuite dans
le conteneur. Les modifications du workspace persistent sur l'hôte ; les
installations manuelles dans le conteneur disparaissent à sa reconstruction.
Ne monter aucun autre dossier hôte ni le socket Docker pour ce socle.

## Outils disponibles

| Élément | Version / choix |
| --- | --- |
| Système | Ubuntu 24.04, image fixée par digest |
| Shell et recherche | Bash et ripgrep |
| Git | 2.43.0, paquet Ubuntu fixé dans le Dockerfile |
| Node.js | 24.21.0 LTS, archive vérifiée par SHA-256 |
| npm | Version livrée avec Node.js |
| OpenSpec | 1.13.2, dépendances verrouillées |

Les fichiers de [.devcontainer](.devcontainer/devcontainer.json) sont la source
de vérité. Le [Dockerfile](.devcontainer/Dockerfile) fixe les paquets directs ;
le [verrou npm](.devcontainer/tools/package-lock.json) fixe les dépendances
OpenSpec. Les dépendances système transitives restent résolues par APT :
ce socle ne promet pas une reconstruction bit à bit. Une version APT retirée
des miroirs nécessite une mise à jour explicite dans une PR.

Pour faire évoluer les outils, modifier leurs versions et empreintes, régénérer
le verrou npm **dans le conteneur** si nécessaire, puis reconstruire et refaire
les vérifications. Aucun Python, SDK .NET, Angular ou Docker imbriqué n'est installé.

## Vérifier le socle

Dans le terminal du conteneur :

```sh
id
git --version
node --version
npm --version
openspec --version
openspec validate --all --strict --no-interactive
git diff --check
```

La procédure complète et les critères attendus sont dans
[docs/validation.md](docs/validation.md). Ces contrôles valident le socle ;
ils ne remplacent pas les futurs tests applicatifs. Aucun workflow GitHub
Actions n'est ajouté pour le moment.

## Spécifications et LLM

[OpenSpec](https://openspec.dev/) structure les propositions, spécifications,
décisions et tâches avant implémentation. Lire le
[guide OpenSpec](docs/openspec.md) et les [instructions agents](AGENTS.md).

[OmniRoute](https://github.com/NStambovsky/OmniRoute) est un candidat pour centraliser
les appels LLM et explorer le routage entre fournisseurs. Son intégration est
uniquement planifiée : aucun service, fournisseur ou compte n'est configuré.
L'évaluation devra mesurer compatibilité, coûts, latence, confidentialité et
comportement en cas d'échec avant adoption. Voir la [feuille de route](docs/roadmap.md).

## Participer

- [CONTRIBUTING.md](CONTRIBUTING.md) : GitHub Flow, review et vérifications.
- [SECURITY.md](SECURITY.md) : bugs et signalements de vulnérabilités.
- [CHANGELOG.md](CHANGELOG.md) : changements non publiés et futures versions.
- [Feuille de route](docs/roadmap.md) : propositions d'issues à relire avant publication.

La licence existante est disponible dans [LICENSE](LICENSE).
