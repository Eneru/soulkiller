#!/usr/bin/env bash
# Explicit operator action from the connected devcontainer.
set -euo pipefail
umask 077

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
for directory in .soulkiller-local .soulkiller-local/models; do
    if [[ -L "$directory" ]]; then
        printf '%s\n' "Model directory must not be a symbolic link." >&2
        exit 1
    fi
    mkdir -p -- "$directory"
done
cd -- .soulkiller-local/models

model=Qwen3-1.7B-Q8_0.gguf
size=1834426016
digest=061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a
revision=90862c4b9d2787eaed51d12237eafdfe7c5f6077
url="https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/$revision/$model"

# Check a regular single-link file and publish only the exact pinned content.
verify() {
    [[ ! -L "$1" && -f "$1" && "$(stat -c '%h %s' -- "$1")" = "1 $size" ]] &&
        printf '%s  %s\n' "$digest" "$1" | sha256sum --check --status --strict
}

if [[ -e "$model" || -L "$model" ]]; then
    if ! verify "$model"; then
        printf '%s\n' "Existing model failed verification. Inspect it before provisioning again." >&2
        exit 1
    fi
else
    temporary=$(mktemp .weights.XXXXXXXX)
    trap 'rm -f -- "$temporary"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    curl -q --fail --location --silent --show-error --max-redirs 5 \
        --proto '=https' --proto-redir '=https' --max-filesize "$size" --max-time 1800 \
        --output "$temporary" "$url"
    verify "$temporary" || { printf '%s\n' "Downloaded model failed verification." >&2; exit 1; }
    ln -T -- "$temporary" "$model"
fi
printf '%s\n' "Pinned model verified."
