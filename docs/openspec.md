# Travailler avec OpenSpec

Le projet utilise [OpenSpec](https://openspec.dev/docs/cli), installé dans le
devcontainer. Sa configuration est [openspec/config.yaml](../openspec/config.yaml).
Le schéma retenu est `spec-driven`. L'initialisation a utilisé
`openspec init --tools none` : les agents suivent [AGENTS.md](../AGENTS.md)
et la CLI, sans dépendre de commandes propres à un assistant.

## Organisation

- `openspec/specs/` contient les exigences de référence intégrées.
- `openspec/changes/<nom>/` contient une évolution proposée, ses deltas
  de spécifications, sa conception et ses tâches.
- `openspec/changes/archive/` accueillera les changements archivés.

Les répertoires de référence et d'archive peuvent être absents tant que le
premier changement n'a pas été intégré. La proposition active
[initialize-repo](../openspec/changes/initialize-repo/proposal.md) décrit le socle ;
elle reste active pendant sa review.

## Cycle de travail

Toutes les commandes suivantes s'exécutent dans le devcontainer.

1. Examiner l'existant avec `openspec list` et `openspec list --specs`.
2. Créer un changement :

   ```sh
   openspec new change nom-du-changement
   openspec status --change nom-du-changement
   openspec instructions proposal --change nom-du-changement
   ```

3. Rédiger `proposal.md`, puis les deltas `specs/<capability>/spec.md`,
   `design.md` et `tasks.md`. Consulter les instructions du schéma :

   ```sh
   openspec instructions specs --change nom-du-changement
   openspec instructions design --change nom-du-changement
   openspec instructions tasks --change nom-du-changement
   ```

4. Faire valider les décisions nécessaires, puis implémenter et vérifier.
   Cocher les tâches uniquement sur preuve, et conserver les décisions dans
   les artefacts versionnés.
5. Valider avant de livrer la PR :

   ```sh
   openspec validate nom-du-changement --strict --no-interactive
   openspec validate --all --strict --no-interactive
   ```

6. Après acceptation de l'implémentation, préparer son archivage sur une branche
   soumise à review :

   ```sh
   openspec archive nom-du-changement
   openspec validate --all --strict --no-interactive
   ```

   Examiner le diff : l'archivage met à jour les spécifications de référence et
   déplace le changement dans l'archive. Il ne remplace pas la review GitHub et
   ne justifie aucun push direct sur `main`.

## Rédaction et validation

La prose est en français. Conserver les structures reconnues par le validateur,
notamment `## ADDED Requirements`, `### Requirement:`, `#### Scenario:`,
`SHALL`, `WHEN` et `THEN`. Chaque exigence décrit un comportement observable
et possède au moins un scénario. La validation structurelle ne démontre pas
que l'implémentation satisfait les exigences : joindre les résultats de tests.

La télémétrie OpenSpec et la vérification automatique de mises à jour sont
désactivées dans l'image. Les montées de version sont explicites et passent
par une PR avec mise à jour du verrou npm.
