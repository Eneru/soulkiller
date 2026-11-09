# Try a sourced answer from the local model

Ask the invented persona Inez a question and inspect the exact source passages.
This experiment uses Qwen3-1.7B on the CPU. Each question starts a temporary
server if it has matching evidence. The command saves no conversation or persona
memory. The [scripted mode](#try-the-pipeline-without-model-weights) also works
with the same evidence and provides predictable examples.

## 1. Build and provision once

Rebuild the Soulkiller devcontainer. From its **connected** terminal, run:

~~~sh
bash tools/models/provision-qwen3.sh
~~~

Allow about 1.71 GiB for the model. The tested Linux x86-64 build uses the
upstream AVX2 and FMA defaults. The provisioner verifies the exact size and
SHA-256 before making it available under the ignored `.soulkiller-local/models/`
directory. A repeat verifies the existing file. An invalid existing file stops
the command so you can inspect it. Model weights are kept outside the image.

## 2. Start the offline trial

In a **host WSL terminal opened in Soulkiller**, build and launch the same image
with the trial limits:

~~~sh
docker build -t soulkiller-dev .devcontainer
docker run --rm -it --init --network none --memory 4g --memory-swap 4g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller" \
  --workdir /workspaces/soulkiller soulkiller-dev bash
~~~

Inside the offline container, prepare the dedicated synthetic evidence. Choose a
new run ID if this one already exists, and use that ID in the following commands.

~~~sh
export PYTHONPATH="$PWD/experiments/text-pdf/src"
python -m soulkiller_text run \
  --corpus experiments/text-pdf/examples/persona-inez --run-id inez-local-001
~~~

## 3. Ask and inspect

~~~sh
python -m soulkiller_text ask --run-id inez-local-001 --profile inez \
  --question "Quelle lampe gardes-tu ?" --evidence-query "lampe bleue" \
  --language fr --local-model
~~~

The expected answer cites `[S1]` and shows the exact excerpt on PDF page 1.
In the recorded trial the model repeatedly failed the citation check for this
question. If you get an accepted answer, check the colour, language and citation
against the excerpt. For English, ask
`What do you collect?` with `paper stars` as the expression and `--language en`.
For a conflict, ask `De quelle couleur est ta lampe ?` with the expression
`lampe` and `--language fr`. Check that the two alternatives are visible and
both cited. The evidence expression is literal and case-sensitive.

No eligible match produces an explicit “I do not know” without starting the
server. The CLI reports a controlled failure if the model returns an invalid
answer or citation, exceeds a limit, or cannot start. It rejects incomplete
saved runs and expressions with more than three matches. Add `--json` for
machine-readable results. Coverage and local timings go to stderr. Run
`exit` when finished to close the offline container.

See the [local trial results](research/local-model-trial.md) for observed output
quality and the [OpenSpec change](../openspec/changes/plan-first-grounded-dialogue/proposal.md)
for the approved scope.

## Try the pipeline without model weights

In the same container and with the same saved run, replace `--local-model` with
`--demo-case lamp` for the French example, `--demo-case paper-stars` for
English, or `--demo-case conflict` for both lamp colours. Scripted mode tests
the evidence and citation path with a fixed response. It can also read the
already saved run from the connected devcontainer.
