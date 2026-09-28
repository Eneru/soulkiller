# Vérifier le socle

Les commandes de développement ci-dessous s'exécutent dans le devcontainer.
Seules la construction et la relance du conteneur se font via Docker ou l'éditeur
sur l'hôte. Conserver les résultats et limites dans la PR.

## Construction et outils

Reconstruire l'image depuis [.devcontainer](../.devcontainer/devcontainer.json)
avec l'éditeur, ou utiliser les commandes hôte du [README](../README.md).

Dans le terminal du conteneur :

```sh
id
pwd
git --version
node --version
npm --version
openspec --version
rg --version
test "$(id -u)" -ne 0
test "$PWD" = /workspaces/soulkiller
test ! -S /var/run/docker.sock
```

Attendus : utilisateur non-root, bon workspace, Git 2.43.0, Node.js v24.21.0,
OpenSpec 1.13.2 et ripgrep 14.1.0. Aucune clé LLM n'est nécessaire.

## Écriture et persistance

Créer un témoin local ignoré, sans écraser un fichier existant :

```sh
test ! -e .soulkiller-local/persistence-check.txt
mkdir -p .soulkiller-local
printf 'soulkiller-persistence-check\n' > .soulkiller-local/persistence-check.txt
```

Recréer le conteneur en conservant le montage Soulkiller, puis vérifier :

```sh
test "$(cat .soulkiller-local/persistence-check.txt)" = soulkiller-persistence-check
test -w .soulkiller-local/persistence-check.txt
```

Après ce contrôle, supprimer uniquement ce témoin si souhaité, depuis le
conteneur. Ne jamais inclure le répertoire local dans un commit.

## Spécifications et dépôt

```sh
openspec list
openspec status --change initialize-repo
openspec validate --all --strict --no-interactive
git diff --check
git diff --cached --check
git diff origin/main -- LICENSE
git status --short
git check-ignore .env .env.local .soulkiller-local/persistence-check.txt .devcontainer/tools/node_modules/example
```

La commande `status --change initialize-repo` concerne cette PR ; après son
archivage, utiliser l'identifiant du changement actif. Le diff de LICENSE doit
être vide. Comparer également son empreinte à celle de la base d'initialisation :

```sh
sha256sum LICENSE
```

Empreinte initiale : `30cd79522ebd85148c43a931036e514e8b5cf8372776be39fc65a2f6293b051c`.

## Relecture des configurations et documents

- Vérifier que devcontainer.json est un JSON valide et correspond au Dockerfile :
  utilisateur, workspace, contexte de construction et commande de démarrage.
- Vérifier que le manifeste et le verrou npm fixent la même version OpenSpec.
- Vérifier les chemins des liens Markdown internes et la cohérence des commandes.
- Vérifier les en-têtes YAML des deux templates d'issues et leurs champs requis.
- Examiner les fichiers suivis : aucun secret, code applicatif, workflow Actions
  ou changement de LICENSE. Les exclusions Git ne remplacent pas cette inspection.
- Après publication, vérifier les branches, le statut draft et le lien de la PR.

## Limites

Cette procédure ne teste pas encore d'application. Le démarrage via l'interface
d'un éditeur et chaque architecture matérielle doivent être distingués des
vérifications faites avec Docker en ligne de commande ; ne pas les annoncer
comme testés sans les avoir exécutés.
