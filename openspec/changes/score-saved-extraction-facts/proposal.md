## Why
After extracting the example, the maintainer needs to see whether its independently
written reference facts were recovered at the expected source locations.

## What changes
Add a read-only score command for saved runs, with readable and JSON reports.
Show exact quote recovery separately from correct TXT offsets/PDF pages, preserve
failed and missing documents in the denominator, and disclose unannotated inputs.
Simplify README to the current usable workflow rather than past implementation steps.

## Scope
Implements part of the approved evaluate-text-pdf-extraction scoring requirement.
No model, retrieval, Docling, performance comparison, automatic quality threshold,
reading-order evaluation or new dependency. PR #23 is confirmed merged.
