# Instructions pour les agents

## Périmètre et environnement

- Travailler uniquement dans le dossier Soulkiller. Ne pas modifier d'autres
  dossiers hôte, les configurations globales hôte ou les paramètres GitHub.
- Exécuter les commandes de développement, Git, installations et vérifications
  dans le devcontainer. Seules les commandes nécessaires à sa construction et
  à son lancement sont autorisées sur l'hôte.
- Ne monter que Soulkiller ; ne pas monter le socket Docker ou des dossiers
  de credentials hôte. Les écritures internes à l'image et au conteneur sont normales.
- Lire les éventuels AGENTS.md plus spécifiques avant de modifier leur périmètre.
- Préserver les changements préexistants et l'historique ; aucun force-push,
  nettoyage destructif ou écrasement sans instruction explicite.
- Ne jamais modifier LICENSE.

## Méthode de travail

- Lire README.md, CONTRIBUTING.md et les spécifications concernées.
- Utiliser OpenSpec via sa CLI et openspec/config.yaml ; ne pas installer de
  configuration globale ou de skills sur l'hôte.
- Pour chaque changement de comportement ou d'architecture, préparer la
  proposition, les spécifications, la conception et les tâches avant de coder.
  Faire valider les décisions produit ou les changements de périmètre par le
  mainteneur ; une demande explicite approuvant un plan vaut autorisation.
- Un correctif documentaire sans effet comportemental peut référencer une
  spécification existante ; expliquer dans la PR si aucune ne s'applique.
- Ne pas inventer les stages de Soulkiller. Python, .NET, Angular et OmniRoute
  sont envisagés, pas adoptés.
- Garder les changements petits et documentés. Préférer rg pour les recherches.
- Documenter en français ; respecter les identifiants et mots-clés imposés par
  les outils, notamment SHALL et WHEN/THEN dans les spécifications OpenSpec.

## Qualité et secrets

- Tester les comportements modifiés, leurs erreurs et leurs limites. Pour les
  futures fonctionnalités, prévoir des tests unitaires, d'intégration et de bout
  en bout adaptés. Les tests courants doivent fonctionner sans clé ni appel LLM payant.
- Ne pas prétendre qu'une vérification a réussi sans l'avoir exécutée ; signaler
  les blocages et distinguer tests du socle et tests applicatifs.
- Exécuter openspec validate --all --strict --no-interactive et git diff --check
  avant livraison ; suivre docs/validation.md pour les changements du devcontainer.
- Ne pas committer de secrets, données personnelles réelles ou journaux sensibles.
  Utiliser des exemples fictifs et des fichiers locaux ignorés.
- Aucun service OmniRoute ou fournisseur LLM ne doit démarrer automatiquement.
- Mettre à jour la documentation et CHANGELOG.md avec le comportement livré.

## GitHub et review

- Suivre GitHub Flow : branche courte depuis main, PR draft, vérifications,
  review humaine, puis fusion manuelle.
- Publier uniquement la branche de travail autorisée. Ne pas fusionner, activer
  l'auto-merge ou modifier les protections du dépôt.
- La PR doit indiquer le changement OpenSpec, les vérifications et leurs limites.
- Les propositions d'issues de docs/roadmap.md attendent la review du mainteneur
  avant création sur GitHub.
- Ne pas marquer une review ou une fusion comme accomplie avant confirmation.
