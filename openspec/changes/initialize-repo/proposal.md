# Proposal

## Why

Soulkiller dispose seulement d'un README initial, d'une licence et d'exclusions Git.
Un socle commun est nécessaire avant de définir les stages et de développer
l'application, afin de rendre le travail reproductible et relisible.

## What Changes

- Ajouter un devcontainer minimal Ubuntu avec utilisateur non-root, Git, Node.js et OpenSpec.
- Initialiser le processus de spécification et les instructions de contribution.
- Documenter le démarrage, la sécurité, les vérifications et les changements.
- Fournir les templates de PR et d'issues ainsi qu'une feuille de route à relire.
- Relier le workspace au dépôt et livrer sur une branche avec PR draft.

Hors périmètre : code applicatif, définition des stages, SDK Python/.NET/Angular,
Docker-in-Docker, intégration active d'OmniRoute, CI et modification de LICENSE.

## Capabilities

### New Capabilities

- `development-foundation` : environnement conteneurisé, validation du socle et contribution guidée par OpenSpec.

### Modified Capabilities

Aucune spécification de référence existante.

## Impact

Le dépôt reçoit des fichiers de documentation et de configuration. La construction
requiert un accès aux registres Ubuntu, Node.js et npm. Aucune API applicative,
migration de données ou consommation de fournisseur LLM n'est introduite.
