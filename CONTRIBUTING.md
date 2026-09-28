# Contribuer à Soulkiller

## Environnement

Lire le [README](README.md) et démarrer le devcontainer avant toute commande.
Les installations et commandes Git se font dans son terminal. Ne modifier
aucun autre dossier hôte ; ne pas toucher à [LICENSE](LICENSE).

L'identité Git et l'authentification restent personnelles. Si elles sont
nécessaires, configurer l'identité au niveau du dépôt avec `git config --local`
et utiliser un mécanisme d'authentification approuvé, sans token dans un fichier
versionné ou une URL de remote. Ne pas copier de credentials dans l'image.

## GitHub Flow

Nous suivons [GitHub Flow](https://blog.stephane-robert.info/docs/developper/version/git/workflows-git/#4-github-flow) :

1. Partir d'un `main` à jour et d'un workspace propre. Ne pas écraser du travail local.
2. Créer une branche courte, par exemple `feature/nom`, `fix/nom` ou `docs/nom`.
3. Préparer les artefacts [OpenSpec](docs/openspec.md), puis implémenter le
   changement autorisé avec ses vérifications et sa documentation.
4. Faire des commits ciblés aux messages explicites et ouvrir une PR **draft**.
5. Indiquer le problème résolu, la référence OpenSpec, les tests réellement
   exécutés et les limites. Demander la review du mainteneur lorsque prêt.
6. Attendre sa validation ; la fusion dans `main` reste manuelle. Aucun auto-merge.

Exemple à exécuter dans le conteneur, depuis un workspace propre :

```sh
git switch main
git pull --ff-only origin main
git switch -c feature/nom-du-changement
```

Si Git refuse la mise à jour, examiner la divergence au lieu de forcer.
Les réglages de protection GitHub ne sont pas configurés par cette initialisation ;
la review reste une règle de contribution.

## Vérifications et documentation

- Suivre [docs/validation.md](docs/validation.md) et valider OpenSpec.
- Ajouter des tests significatifs pour chaque comportement applicatif futur :
  succès, entrées invalides, erreurs des dépendances et régressions.
- Utiliser des doublures LLM déterministes pour les tests ordinaires ; réserver
  les essais externes à une exécution explicite avec budget et secrets locaux.
- Mettre à jour README, guides et [CHANGELOG](CHANGELOG.md) selon le changement.
- Ne cocher une tâche que lorsque son résultat est vérifié.

Aucune CI n'est créée dans cette PR. Les preuves locales doivent figurer dans la
description de PR ; une CI minimale pourra être proposée séparément.

## Issues et sécurité

Utiliser les templates de bug et de fonctionnalité pour les demandes ordinaires.
La [feuille de route](docs/roadmap.md) contient des propositions non encore publiées.
Les vulnérabilités suivent exclusivement [SECURITY.md](SECURITY.md).
