## Approach
Score independently authored annotations from the saved manifest, never from the
current corpus. Preserve read_saved_run's public interface while exposing an
additional reader returning saved specifications, including those for missing rows.
Reuse strict framed store/manifest/fixture validation; no parsing or writes.

Match exact Unicode code points: no normalization, case folding or whitespace
changes. TXT recovery means the quote appears somewhere; location correctness
requires an exact match at its declared start/end. Prefer that reference location
when repeated; otherwise show the first occurrence. PDF recovery searches retained
pages separately, never joins pages. Prefer the annotated page when present;
otherwise report the first retained page containing the quote. Report one resolving
location (zero-based, end-exclusive offsets) per annotation, bounding report growth.
A partial PDF can recover a fact while remaining visibly partial.

Keep all annotations in totals, including failed/unfinished/missing documents.
Unknown observations yield no recovered fact, never absence of an expected fact.
Missing observations count as unknown outcomes, not outcome matches. Compare saved
outcomes to expected outcomes separately from quote metrics. Report unannotated
document count and no-annotation totals as 0/0, not 100%. Run status remains visible.

The command succeeds when a complete saved run is scored, even with quality
mismatches; it is not an unapproved quality gate. Incomplete/failure/cancellation
exit semantics stay those of show. Reuse terminal escaping and exact JSON.
No environment/editor/image/CI changes: existing Python runtime, native editor and
all-source tests/scans cover the new modules. No benchmark or Windows claim.
