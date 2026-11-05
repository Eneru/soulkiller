# First sourced-answer experiment

**Status: approved in PR #27; scripted ask is the first implementation. Real-model execution is pending.**

## ADDED Requirements

### Requirement: Explicit source-scoped question

The experiment SHALL accept one explicit synthetic persona profile,
saved run, question, literal evidence expression and fr/en answer language.
It SHALL use a dedicated attributed corpus and profile-selected fixture IDs,
validate saved evidence and disclose source coverage before invoking a model.
Incomplete, unavailable or truncated eligible evidence SHALL stop generation.
It SHALL NOT infer persona identity from a filename or source ownership.

#### Scenario: Ask the invented Inez about her lamp
- **WHEN** Inez's eligible saved sources contain the requested lamp passage
- **THEN** only those source excerpts can enter the request and the selected answer language is explicit

#### Scenario: Another persona has a unique fact
- **WHEN** the selected run also contains another persona's marker source
- **THEN** that source does not enter Inez's model context or citations

### Requirement: First-person answer and inspectable citations

Generated answers SHALL be instructed to speak in the selected persona's first
person using supplied evidence, preserving explicit third-party attribution.
The tool SHALL distinguish generated text from exact local source quotations
and provide resolving revision/page/offset references for accepted citation IDs.
It SHALL reject invalid or unsupported response structure instead of displaying
model-invented references as accepted evidence.

#### Scenario: A response cites a supplied fact
- **WHEN** an otherwise valid answer references [S1]
- **THEN** the operator can inspect the exact locally retained excerpt and its source location

#### Scenario: A model invents a citation
- **WHEN** an answer references an ID outside the supplied evidence
- **THEN** the response fails validation rather than gaining an invented source

### Requirement: Visible uncertainty and conflict evaluation

No matching eligible evidence SHALL produce explicit uncertainty without a
model call, limited to the available retrieval scope. Trial instructions SHALL
require unknown information to remain unknown and conflicting sources to be
presented with both citations without an automatic winner.
Real-model evaluation SHALL record semantic/attribution failures separately from
mechanical citation validity; citation resolution SHALL NOT be called proof of truth.

#### Scenario: A question has no retrieved evidence
- **WHEN** the evidence expression yields no eligible passages
- **THEN** the tool reports uncertainty without contacting a model or claiming complete knowledge coverage

#### Scenario: Two supplied facts disagree
- **WHEN** the trial supplies conflicting lamp-colour facts
- **THEN** the evaluation checks that both alternatives and citations remain visible and records any automatic resolution as a quality failure

### Requirement: Bounded explicit local execution

Provisioning and real inference SHALL require explicit operator actions and the
reviewed pinned asset/profile. The local trial SHALL run offline within its
declared CPU/memory/time/token/output limits, with visible failures and owned
process cleanup. It SHALL NOT start at container startup or in routine CI,
download replacement assets, execute source instructions or use a remote fallback.

#### Scenario: The model is absent or unavailable
- **WHEN** the local trial cannot use its approved asset/runtime
- **THEN** it fails visibly without fetching a substitute or sending the request elsewhere

### Requirement: Trial state and review boundaries

This trial SHALL keep source evidence, generated output and approved persona
metadata distinct. It SHALL NOT persist conversational memory or infer style
changes. Accepted future automatic-memory requirements remain in force.
Any remote trial SHALL require separately approved endpoint, data/retention
terms and cost limits; local observations SHALL NOT claim native Windows performance.

#### Scenario: A generated answer invents a preference
- **WHEN** an unsupported preference appears in trial output
- **THEN** it is recorded as an evaluation failure and cannot become a source fact or saved persona memory
