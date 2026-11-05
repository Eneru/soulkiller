## Status and implementation boundary

Proposed, pending maintainer review. The comparison and artifact inventory are in
[the decision brief](../../../docs/research/first-dialogue-inference-comparison.md).
This extends the experimental Python CLI, not a production-language decision.

## Evidence and identity

Use a dedicated invented Inez corpus/profile: the existing mixed example has
generic subject labels and must not silently become a persona. Explicit fixture
IDs in a reviewed profile select Inez evidence. Include third-party text and a
second-persona marker as negative controls; filenames/ownership are not identity.
Validate the saved run fully before filtering. No cross-run/persona auto-discovery.

Reuse literal search with its query and excerpt bounds, scoped to eligible
fixtures. Ask takes a separate question, explicit evidence expression and required
fr/en answer language. Reject an incomplete run, unavailable eligible document or
truncated evidence selection before model invocation; no silent context omission.
No passages gives deterministic uncertainty without contacting the model.

## Answer contract

Provide a system instruction, a separate data-only evidence section with request
IDs [S1]..[S3], the explicit persona label and the question. Imported instructions
are evidence, never tools or application permissions. Source files/paths, keys and
the rest of the corpus are not model inputs. Labels remain unverified metadata.

Require bounded structured final content: status (answer/uncertain/conflict),
short answer text and citation IDs. Reject unknown/duplicate IDs, malformed or
oversized responses, non-final/truncated content and tool/function requests.
An answer/conflict needs citations; conflict needs both source alternatives.
Render exact excerpts/ranges from local accepted evidence, never model-supplied
quotations, paths or links. Always distinguish generated text from source text.

Mechanical validation proves source resolution, not factual entailment. Evaluate
real outputs with the independent human rubric; record unsupported claims and
failures rather than asserting that valid JSON/citations guarantee truth.
Do not promote model output into source facts, memories or a style profile.

## Local runtime and limits proposed for approval

Build llama.cpp v0.9.0 from its full source commit in the brief, CPU-only inside
the Ubuntu devcontainer. Freeze/verify the source artifact and dependency/license/
advisory inventory before compiling; exercise the actual installed binary.
Do not assume release binaries match Ubuntu 24.04 or the user's CPU instruction set.
Add runtime/editor-path/validation guidance with the integration; Python native
editor tooling remains applicable. No authored C++ component is proposed.

Explicit provisioning writes only the pinned model under ignored
.soulkiller-local/models/ and checks upstream-declared SHA-256/size before use.
A partial/mismatched asset fails; no model-id/latest lookup or automatic replacement.
Start an owned single-model server only for an explicit local trial, on container
127.0.0.1 without a host port; stop/reap it on completion/cancellation/error. Refuse an occupied endpoint or
model mismatch; never stop/reuse an unrelated process.
Run generation with Docker network-none, only Soulkiller mounted, no socket.
No remote URL, redirect, ambient proxy, router, web UI or tool/MCP execution.

Experimental guards: one request, 2 CPU threads, 4 GiB container RAM, 2048 context
tokens including at most 128 output tokens, 180 seconds per request and 64 KiB
response cap. Check tokenized prompt fit with the pinned template; never truncate
evidence to fit. Disable thinking in the verified template, fix/record sampling
settings and seed, and reject unsupported options rather than guess compatibility.
These are trial stop conditions, not minimum hardware or acceptable latency.

## Tests, trial and delivery

Use a narrow model-adapter seam with deterministic doubles in routine tests/CI;
contract tests cover transport, timeouts, invalid output, citations and cleanup.
Keep all-source >=70% executable-line coverage, function docs, current static/
secret/dependency gates and existing PR-main/SemVer-only CI. No real weights or
inference in routine CI. Review HTTP-boundary and ZAP applicability with the local
third-party server integration under issue #7; a mock scan is not its security proof.

Run the six scenarios in the comparison and two repeats of each supported-language
question: at most 10 generation requests, 30 minutes total. Missing-evidence
abstention consumes no generation request. Record all failures/unrun cases.
Any retained synthetic trial report uses a new ignored, create-only local run
folder and keeps generated text distinct from immutable source evidence.
Public reports use only approved project profiles/limits. Operator-specific
hardware/network inventory stays ignored and local; withheld details are labeled
undisclosed, never replaced with fabricated reference-machine measurements.
Measure raw startup/answer time, token counts and process/container memory scope;
compare only declared conditions. Owned/hosted remote execution is still blocked
on its separate endpoint/data/budget approval. No Windows performance claim.
