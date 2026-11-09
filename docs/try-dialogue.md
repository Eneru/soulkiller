# Try a sourced answer from the invented Inez persona

Start with the scripted walkthrough to verify that the dialogue command resolves
citations to exact saved passages. The optional Qwen3 experiment reproduces a
known citation rejection. Both modes use the same synthetic evidence. The
command saves no conversation or persona memory.

## 1. Prepare the saved evidence

In a **host WSL terminal opened in Soulkiller**, build and launch the offline
devcontainer. The resource limits also cover the optional Qwen3 experiment.

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

## 2. Verify the citation walkthrough

~~~sh
python -m soulkiller_text ask --run-id inez-local-001 --profile inez \
  --question "Quelle lampe gardes-tu ?" --evidence-query "lampe bleue" \
  --language fr --demo-case lamp
~~~

Expect the fixed answer `Je garde une lampe bleue. [S1]` and the exact excerpt
from PDF page 1. This mode exercises source selection, citation validation and
display using a scripted response. It can also read the already saved run from
the connected devcontainer.

For English, ask `What do you collect?` with `paper stars` as the evidence
expression, `--language en` and `--demo-case paper-stars`. To see both lamp
colours and citations, ask `De quelle couleur est ta lampe ?` with `lampe`,
`--language fr` and `--demo-case conflict`. The evidence expression is literal
and case-sensitive.

## 3. Optional Qwen3 experiment

If the model is absent, run the provisioner from a **connected** Soulkiller
devcontainer terminal. Both containers share the same Soulkiller folder.

~~~sh
bash tools/models/provision-qwen3.sh
~~~

Allow about 1.71 GiB for the model. The tested Linux x86-64 build uses the
upstream AVX2 and FMA defaults. The provisioner verifies the exact size and
SHA-256 before making it available under the ignored `.soulkiller-local/models/`
directory. A repeat verifies the existing file. An invalid existing file stops
the command so you can inspect it. Model weights are kept outside the image.

Back in the offline terminal, reproduce the French lamp trial:

~~~sh
python -m soulkiller_text ask --run-id inez-local-001 --profile inez \
  --question "Quelle lampe gardes-tu ?" --evidence-query "lampe bleue" \
  --language fr --local-model
~~~

The recorded runs reached `Local model generation` and then returned
`Dialogue failed: invalid_model_citations`. This sequence means the CPU server
generated text and the CLI rejected its citations. Use the scripted walkthrough
above to inspect the evidence for the same question. The
[local trial results](research/local-model-trial.md) detail the other cases.

No eligible match produces explicit uncertainty without starting the server.
Both modes reject incomplete saved runs and expressions with more than three
matches. Add `--json` for machine-readable results. Evidence counts and local
timings go to stderr. Run `exit` when finished to close the offline container.

The [OpenSpec change](../openspec/changes/plan-first-grounded-dialogue/proposal.md)
defines the approved scope.
