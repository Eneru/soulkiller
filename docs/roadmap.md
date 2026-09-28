# Feuille de route proposée

Ces éléments sont des **brouillons d'issues**, à relire dans la PR d'initialisation.
Aucune issue n'est créée automatiquement. Après validation, les publier et
remplacer leurs identifiants locaux par les liens GitHub. L'ordre ci-dessous
exprime les dépendances ; il ne constitue pas une définition des stages produit.

## R1 — Définir les stages et le premier parcours

**Objectif :** préciser ce que Soulkiller doit faire, pour qui, avec quelles
données d'entrée et quels résultats observables. Distinguer l'inspiration
fictionnelle des capacités réellement visées.

**Dépendances :** review du socle d'initialisation.

**Livrables et acceptation :**

- [ ] Public, problème, premier parcours et exclusions validés par le mainteneur.
- [ ] Stages nommés et décrits avec entrées, sorties et conditions de passage.
- [ ] Besoins de stockage, confidentialité, consentement et suppression des données définis.
- [ ] Exemples fictifs et critères observables documentés dans un changement OpenSpec.

## R2 — Choisir l'architecture et les langages

**Objectif :** choisir la structure minimale permettant le premier parcours.

**Dépendances :** R1.

**Livrables et acceptation :**

- [ ] Responsabilités des composants et échanges définis.
- [ ] Décision argumentée sur Python, .NET et l'éventuel frontend ; aucune pile imposée par avance.
- [ ] Stockage et contrats nécessaires au parcours spécifiés.
- [ ] Outils et versions ajoutés au devcontainer ; démarrage local documenté et vérifié.

## R3 — Établir la stratégie de tests reproductibles

**Objectif :** rendre le premier parcours et ses erreurs testables depuis le devcontainer.

**Dépendances :** R1 et R2.

**Livrables et acceptation :**

- [ ] Répartition des tests unitaires, d'intégration et de bout en bout définie.
- [ ] Doublures LLM déterministes, jeux de données fictifs et isolation des tests définis.
- [ ] Commande de test reproductible sans fournisseur externe ni coût LLM.
- [ ] Décision explicite sur le besoin de Docker-in-Docker ; ajout uniquement si justifié.
- [ ] Proposition éventuelle de CI minimale avec estimation de consommation Actions.

## R4 — Évaluer OmniRoute et les accès LLM

**Objectif :** décider si [OmniRoute](https://github.com/NStambovsky/OmniRoute)
convient aux besoins identifiés.

**Dépendances :** R1 et R2 ; les essais reproductibles s'appuient sur R3.

**Livrables et acceptation :**

- [ ] Version évaluée, licence et interfaces réellement compatibles documentées.
- [ ] Comparaison avec l'accès direct à un fournisseur et critères d'adoption.
- [ ] Mesures de latence, consommation et coûts sur un scénario représentatif.
- [ ] Erreurs, limites de débit, délais, retries et bascule de fournisseur évalués.
- [ ] Flux de données, journaux, stockage de secrets et règles de confidentialité examinés.
- [ ] Décision d'adoption ou de rejet relue ; aucun secret ni appel payant automatique.
- [ ] Si adopté : service local optionnel, configuration et procédure de test documentés.

## R5 — Livrer le premier incrément fonctionnel

**Objectif :** implémenter une tranche complète du parcours choisi en R1.

**Dépendances :** R1, R2, R3 et décision R4 lorsque le parcours utilise des LLM.

**Livrables et acceptation :**

- [ ] Proposition, spécifications, conception et tâches OpenSpec relues.
- [ ] Parcours exécutable entièrement depuis le devcontainer.
- [ ] Scénarios nominaux, données invalides et indisponibilité des dépendances testés.
- [ ] Documentation d'usage et CHANGELOG à jour.
- [ ] PR accompagnée des résultats de tests, puis fusion seulement après review humaine.
