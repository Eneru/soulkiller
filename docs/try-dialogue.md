# Try the first sourced-answer demo

The current experiment validates one question, selects exact saved passages and
shows a scripted response beside its local sources. Choose the script explicitly:
this is a testable dialogue pipeline, with real-model generation scheduled for
the next integration. No conversation or persona memory is saved.

## Prepare the invented sources

Follow the [offline extraction launch](try-extraction.md#1-open-the-offline-environment)
to rebuild the devcontainer and start it. The updated Ubuntu package pins are
required for a fresh build. Inside the offline container:

~~~sh
export PYTHONPATH="$PWD/experiments/text-pdf/src"
python -m soulkiller_text run \
  --corpus experiments/text-pdf/examples/persona-inez --run-id inez-demo-001
~~~

Use a new run ID if that one exists. This dedicated synthetic corpus has invented
author/subject labels and a second-persona control. The Inez profile selects fixed
fixture IDs, revisions and attribution labels. The ordinary mixed extraction
example is not an Inez profile.

## Ask and inspect

~~~sh
python -m soulkiller_text ask --run-id inez-demo-001 --profile inez \
  --question "Quelle lampe gardes-tu ?" --evidence-query "lampe bleue" \
  --language fr --demo-case lamp
~~~

Expect a scripted first-person answer and [S1] with the actual excerpt on page 1.
The command first reports eligible coverage and matching passages. The evidence
expression is literal and case-sensitive; the question is kept separate.
The selected script does not interpret the question. The application validates
citations and renders exact stored excerpts, which can be checked with show/search.

To see a conflict, use the expression "lampe" and the demo case conflict:
both page references remain visible. For English, use "paper stars",
language en and demo case paper-stars. The third-party script with "glass marbles"
retains Corin's attribution. An absent expression returns "I do not know" (or
"Je ne sais pas") without invoking even the scripted collaborator.

Ask accepts --json for machine-readable output; coverage is announced on stderr.
It runs in the ordinary connected devcontainer too, using only saved evidence.
A complete run and all approved eligible documents are required; broad expressions
with more than three matches fail; choose a narrower expression. Corruption,
unavailable evidence and invalid model responses yield a controlled failure.
Question arguments are bounded to 500 nonblank code points.

These are invented examples. The [approved dialogue contract](../openspec/changes/plan-first-grounded-dialogue/proposal.md)
defines the subsequent real local trial and its separate quality evaluation.
