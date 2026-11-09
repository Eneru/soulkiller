# Try a sourced answer from the invented Inez persona

Start with the scripted walkthrough to verify that the dialogue command resolves
citations to exact saved passages. The optional Qwen3 comparison uses the same
synthetic evidence to test two citation formats. The command saves no
conversation or persona memory.

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

## 3. Compare citation formats with Qwen3-1.7B

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

Back in the offline terminal, compare the baseline and structured format:

~~~sh
for mode in --local-model --local-model-structured; do
  python -m soulkiller_text ask --run-id inez-local-001 --profile inez \
    --question "Quelle lampe gardes-tu ?" --evidence-query "lampe bleue" \
    --language fr "$mode"
done
~~~

For the baseline, the recorded French and English runs returned
`invalid_model_citations` with `inline_id_mismatch`. Their prose omitted markers
for the IDs in the list. In the structured format Soulkiller renders the
markers from the validated IDs. The recorded French answer was
`Je garde une lampe bleue. [S1]`, followed by the exact excerpt on PDF page 1.

Use the English and conflict questions from step 2 with the same two model
flags. Check both colours and whether the answer describes a disagreement
about one lamp. In the comparison both formats resolved the citations but
described two lamps. See the [paired trial results](research/structured-dialogue-trial.md)
for the full matrix.

No eligible match produces explicit uncertainty without starting the server.
All modes reject incomplete saved runs and expressions with more than three
matches. Add `--json` for machine-readable results. Evidence counts and local
timings go to stderr.

## 4. Compare the two models on the conflict

Provision the 4B artifact from a connected Soulkiller devcontainer terminal:

~~~sh
bash tools/models/provision-qwen3.sh qwen3-4b
~~~

The candidate needs an additional 2.33 GiB of storage. The provisioner verifies
the pinned bytes and keeps the 1.7B file available for the comparison. Back in
the offline terminal from step 1, run:

~~~sh
for mode in --local-model-structured --local-model-4b; do
  python -m soulkiller_text ask --run-id inez-local-001 --profile inez \
    --question "De quelle couleur est ta lampe ?" --evidence-query "lampe" \
    --language fr "$mode"
done
~~~

Check whether each answer explains that the sources disagree on the colour of
one lamp and shows both passages. A reply that describes two lamps fails this
case even if its citations resolve. The 4B candidate uses the same structured
citation contract and resource limits. The
[model comparison report](research/local-model-comparison.md) records the
observations. Run `exit` when finished to close the offline container.

The [OpenSpec change](../openspec/changes/plan-local-model-comparison/proposal.md)
defines the scope of the model comparison.
