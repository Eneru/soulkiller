# Design

## Context

Le dossier local était vide. Le dépôt public Eneru/soulkiller sur main contient
LICENSE, un README court et un gitignore Python. L'intégration Docker WSL est
nécessaire pour respecter la contrainte d'exécution dans un conteneur.

## Goals / Non-Goals

Fournir un environnement minimal reconstruisible et un processus de contribution
avec spécifications, vérifications et review humaine. Ne pas choisir les stages,
l'architecture applicative ou les fournisseurs LLM pendant cette initialisation.

## Decisions

- Utiliser Ubuntu 24.04 par digest et son utilisateur ubuntu non-root. Seul le
  workspace Soulkiller est monté ; pas de mode privilégié ni de socket Docker.
- Installer Node.js 24.21.0 depuis l'archive officielle avec empreinte SHA-256
  pour amd64 ou arm64. Verrouiller OpenSpec 1.13.2 et ses dépendances dans
  .devcontainer/tools/package-lock.json, sans projet npm applicatif.
- Fixer les paquets directs Ubuntu. Les dépendances APT transitives restent
  celles des miroirs, ce qui exclut une garantie de reproductibilité bit à bit.
- Utiliser openspec init --tools none et AGENTS.md comme point d'entrée des agents.
  Les spécifications décrivent le comportement de l'environnement de développement.
- Fournir une procédure de validation Markdown, sans ajouter de scripts ou de CI.
- Décrire OmniRoute et les futures issues dans la feuille de route ; leur
  activation/publication attend une review distincte.
- Conserver le changement OpenSpec actif jusqu'à acceptation. L'archivage
  ultérieur mettra à jour les spécifications de référence via une PR.

## Risks / Trade-offs

- Les miroirs peuvent retirer des versions APT : une PR mettra à jour les
  versions concernées au lieu de les remplacer silencieusement.
- Les montages Windows peuvent différer des permissions Linux natives.
  Vérifier l'écriture avec l'utilisateur non-root ; les clients Dev Containers
  peuvent adapter son UID à l'hôte.
- L'initialisation n'active pas de protection GitHub imposant une review :
  cette exigence est documentée et appliquée dans le workflow.
- Les vérifications du socle ne constituent pas une suite de tests applicatifs.
  Celle-ci sera construite avec les fonctionnalités.

## Migration Plan

Cloner le dépôt existant sans modifier LICENSE, travailler sur
feature/initialize-repo, vérifier localement puis ouvrir une PR draft vers main.
Aucune migration de données ou modification des paramètres GitHub.
Avant fusion, abandonner la PR suffit à conserver main inchangé.

## Open Questions

Les stages, l'architecture et l'adoption d'OmniRoute sont volontairement confiés
aux propositions de la feuille de route. Ils ne bloquent pas ce socle.
