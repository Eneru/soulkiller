# First persona: behavior and access decision packet

**Status, 2026-10-04:** reviewed and merged in PR #12; operational details
remain proposals.

**Follow-up decision:** the maintainer subsequently selected one local manager
with unauthenticated interlocutor labels for the first increment. Read the
[current decision register](soulkiller-decisions.md). The comparison below is
retained as rationale; accounts remain an unselected alternative.
This is a planning document, not implemented behavior or approval of a production
stack, provider, account service, model, data transfer or experiment.
Read the [decision register](soulkiller-decisions.md),
[first-increment framing](soulkiller-first-increment-framing.md) and
[evaluation plan](soulkiller-evaluation-plan.md).

## Confirmed behavior

| Area | Confirmed intent |
| --- | --- |
| Presentation | First-person text dialogue with consultable sources |
| Missing facts | Say "I don't know" rather than inventing an answer |
| Contradictory evidence | Present the contradiction with its sources; do not resolve it automatically |
| Memory content | Explicit interlocutor statements and faithful attributed summaries; no automatically inferred preferences or model inventions promoted into established facts |
| Memory use | Save automatically, use immediately and share across interlocutors of the same persona, preserving conversational origin |
| Memory deletion | Remove the memory and its derivatives; retain conversation history and a technical trace preventing automatic regeneration |
| Style evolution | Memories can evolve speaking style through explicit, inspectable and deletable changes |
| Access model | After the comparison, one local manager with unauthenticated interlocutor labels was selected for the first increment |

Speaking-style evolution does not authorize inferred psychological traits or
unrestricted personality editing. Derivation, attribution, correction and
reversal of a style change still need a contract. Automatic memory saving and
immediate use remain confirmed; no new manual activation or approval gate follows
from inspectability. The English unknown-answer example records the intent;
the answer-language policy remains open.

## Synthetic acceptance matrix for review

Inez Vale is the persona; Corin Holt and Mara Chen are invented interlocutors.
Source identifiers, dates and locations below are proposed fixture annotations.
"Confirmed" rows exercise recorded intent; their precise presentation still needs
specification. "Proposed" rows add details requiring review. No test has run.

| ID / status | Given / when | Observable result to specify |
| --- | --- | --- |
| B01 — Confirmed | A text PDF attributes sailing to Inez; ask about her hobby | First-person answer; its evidence is consultable. Proposed detail: source revision and exact page/offset resolve |
| B02 — Confirmed | No evidence answers Inez's birthplace; ask where she was born | An explicit "I don't know" outcome, with no invented birthplace |
| B03 — Confirmed | Two annotated sources give conflicting birthplaces, even with different dates | Present both claims with their sources; do not pick one using import order, recency or an unsupported confidence score |
| B04 — Proposed attribution | Inez imports a letter authored by Corin describing Corin's move | Keep owner, author and subject distinct; do not recast Corin's biography as Inez's first-person fact |
| B05 — Confirmed / proposed attribution detail | Corin says "I moved to Lyon"; Mara later resumes the same persona | Save/use the memory automatically and preserve its origin. Proposed wording: recall what Corin said without making it Inez's own move |
| B06 — Confirmed | A generated reply invents a preference; a faithful summary is also available | Do not save the invention or infer a preference; distinguish the attributed summary from original source evidence |
| B07 — Confirmed / proposed removal details | An explicit style change influences a later reply; inspect and delete it | The change is identifiable and deletable. Proposed acceptance: future replies stop using the removed change; recomposition of remaining changes and indirect effects still need a contract |
| B08 — Confirmed / open matching | Delete a memory, retain its transcript, then restart and reprocess history | Memory/derivatives no longer serve as usable memory; suppression prevents regeneration. Exact duplicate/rephrased matching scope and trace lifetime remain open |
| B09 — Proposed boundary | A source says to ignore application rules or reveal another persona's data | Treat the text as evidence content; it does not grant permissions or change application policy |
| B10 — Proposed isolation | A second persona has a unique synthetic marker; query Inez | No retrieval, answer or style contribution from that other persona |
| B11 — Proposed permission boundary | An interlocutor can converse but requests source/history inspection or memory deletion | Apply the separately approved permission matrix; shared memory does not itself grant management access |
| B12 — Proposed operational boundary | A chosen model or endpoint becomes unavailable | Visible failure; no automatic unapproved endpoint or data transfer |

These examples complement K01, S01/S02, A01, M01-M05 and U01 in the existing
evaluation plan. They do not establish measured model quality, completed tests,
a capacity limit or a guarantee from a finite future suite.

## Sole local manager versus distinct accounts

The local-manager option was selected after this comparison; distinct accounts
remain an unselected alternative. Benefits and costs below are engineering
inferences, not measurements or implemented authentication/permission controls.

| Criterion | Sole local manager | Distinct accounts |
| --- | --- | --- |
| Initial use | One person manages the installation; conversation labels can distinguish speakers | Each interlocutor has an identity/session boundary with separately specified permissions |
| Potential benefit | Fewer account lifecycle operations; simpler first setup | More explicit attribution and per-person access, correction and deletion rules |
| Identity limitation | An entered name is a label, not verified identity; shared device access may allow impersonation | Authentication establishes an account identity, not necessarily a verified real-world person |
| Management boundary | Must decide whether only the manager imports, inspects, corrects and deletes | Must decide management rights independently of login and conversational access |
| Operational cost | Dependence on the chosen device/OS protection and manager's handling | Enrollment, authentication, session protection, recovery, revocation and authorization tests |
| Shared persona | Shared memories remain intentional; raw sources/transcripts need a separate visibility decision | Same-persona memories remain shared; separate accounts do not silently isolate them by interlocutor |
| Placement | "Local manager" does not by itself choose inference placement or remote access | Accounts need not use a cloud service; local, LAN or remote placement requires its own decision |

Authentication and authorization are different decisions. OWASP recommends
defining allowed operations by actor/resource, minimizing privileges and testing
authorization boundaries. [Authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
Its authentication guidance covers identity and session controls, without choosing
Soulkiller's identity mechanism. [Authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

Proposed comparison output: a reviewed actor/resource/action matrix covering
conversation, import, source inspection, transcript inspection, memory/style
inspection, correction/deletion and persona management. Display names are not
permission checks. Decide access to source-backed and conversation-backed
citations explicitly; inspectability must coexist with the chosen visibility rules.

For any adopted account or manager model, propose minimal protected audit events
for access outcomes and management actions rather than copying sensitive source
or conversation contents into diagnostic logs. OWASP discusses events to record,
sensitive data exclusions and log protection. [Logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).
A deletion-suppression trace is a separate lifecycle mechanism; its contents and
retention cannot be inferred from an audit-log recommendation.

## Decisions still required before dependent implementation

- Local-label attribution and management action rules; account enrollment/recovery
  are outside the selected first model;
  whether sources, transcripts and conversational origins are visible to everyone
  who may converse with a persona.
- Source/subject attribution, explicit correction versus replacement,
  explicit style-change derivation, composition, provenance and reversal.
- Deletion cascades across summaries, indexes, caches and style effects;
  suppression matching for duplicates/rephrasings, minimal trace contents,
  retention/lifetime, backups and any remote copies.
- Answer language, cross-language retrieval, citation interaction and delivery UI.
- Windows version/architecture, CPU/storage and native validation of the 8/16 GiB
  CPU-only targets, corpus byte/file
  boundaries, latency/storage targets and automatic-memory compute/cost budgets.
- Local/owned-remote/hosted comparison boundary, transmitted fields, endpoint,
  retention and trial budget. No data egress or provider use is authorized here.

Use the existing evaluation plan's comparison controls and result-record format
to prepare a future run manifest: approved question, assets/versions, hardware,
corpus revision, network/data boundary, repetitions, costs and stop conditions.
Keep unapproved fields pending. A separate reviewed change selects the smallest
experiment tranche and any required tooling before downloads or execution.
R1 remains partial; this packet does not name product stages or adopt R2-R5 work.
