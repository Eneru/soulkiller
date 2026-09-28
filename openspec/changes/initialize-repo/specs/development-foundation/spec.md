## ADDED Requirements

### Requirement: Environnement de développement conteneurisé
Le dépôt SHALL fournir un devcontainer Ubuntu 24.04 incluant Git, Node.js 24.21.0
et OpenSpec 1.13.2, avec versions explicites et utilisateur non-root.

#### Scenario: Démarrage depuis le dépôt
- **WHEN** un contributeur construit et démarre l'environnement documenté
- **THEN** il dispose d'un terminal non-root dans /workspaces/soulkiller et peut exécuter Git, Node.js et OpenSpec

#### Scenario: Persistance du workspace
- **WHEN** le contributeur écrit un fichier dans le workspace puis recrée le conteneur
- **THEN** le fichier conserve son contenu et reste modifiable par l'utilisateur de développement

#### Scenario: Archive Node.js incorrecte
- **WHEN** l'empreinte de l'archive Node.js ne correspond pas à celle fixée
- **THEN** la construction échoue avant l'installation de cette archive

### Requirement: Périmètre minimal sans service implicite
L'environnement SHALL démarrer sans service applicatif, fournisseur LLM, socket
Docker monté ou privilèges Docker supplémentaires ; le dépôt SHALL ne pas ajouter
de workflow GitHub Actions pendant l'initialisation.

#### Scenario: Démarrage du socle
- **WHEN** le devcontainer démarre avec sa configuration versionnée
- **THEN** aucun appel LLM ni service OmniRoute n'est déclenché et aucun secret fournisseur n'est requis

### Requirement: Processus OpenSpec et review
Le dépôt SHALL fournir une configuration OpenSpec spec-driven, les artefacts du
changement d'initialisation et des instructions de contribution imposant une
review humaine avant fusion.

#### Scenario: Vérification des spécifications
- **WHEN** le contributeur lance openspec validate --all --strict --no-interactive
- **THEN** les artefacts d'initialisation sont reconnus et valides

#### Scenario: Livraison de l'initialisation
- **WHEN** le changement est soumis au mainteneur
- **THEN** une PR draft propose feature/initialize-repo vers main, sans fusion automatique

### Requirement: Documentation et suivi
Le dépôt SHALL documenter son état, le démarrage, les contributions, le signalement
des bugs et vulnérabilités, les changements et la feuille de route ; il SHALL
fournir des templates Markdown de PR et d'issues.

#### Scenario: Préparer les prochaines étapes
- **WHEN** le mainteneur lit la feuille de route
- **THEN** chaque proposition indique un objectif, des dépendances et des critères d'acceptation sans prétendre qu'une issue est déjà publiée

#### Scenario: Vulnérabilité suspectée
- **WHEN** un contributeur consulte SECURITY.md
- **THEN** il est orienté vers un canal privé disponible ou une demande de canal sans divulgation publique de détails sensibles

### Requirement: Préservation de la licence
L'initialisation SHALL conserver LICENSE octet pour octet et préserver l'historique
du dépôt existant.

#### Scenario: Inspection du changement
- **WHEN** le mainteneur compare la branche d'initialisation à sa base main
- **THEN** LICENSE est inchangé et le commit de base demeure un ancêtre de la branche
