## Review

- [x] Confirm PR #33 merge and use its 4B results to select a comparison control.
- [x] Prepare the scope, data boundary, acceptance criteria and stop conditions.
- [x] Obtain maintainer approval of the implementation scope (PR #34).

## Local worker simulation

- [x] Add the versioned protocol and explicit synthetic-only client and one-shot scripted worker.
- [x] Test the real subprocess, no-call paths, tampered evidence, output limits, timeout and local citation validation.
- [x] Verify the conflict and no-match walkthroughs inside the offline devcontainer.
- [x] Obtain maintainer review of the simulation (PR #35).

## Pinned worker runtime

- [x] Add a one-shot worker with pinned offline inference and a deadline covering input, execution and output.
- [x] Verify request confinement, non-networked inference and child cleanup with credential-free tests.
- [x] Run the real 4B worker for one synthetic case in the offline devcontainer and resolve the citations.
- [ ] Obtain maintainer review of the pinned worker.

## SSH transport implementation

- [ ] Add an authenticated SSH client for the one-shot worker.
- [ ] Validate identity failures, deadlines and disconnect cleanup against container-local test doubles.
- [ ] Validate dependency pins and editor, CLI and CI checks without contacting a real endpoint.

## Separate live trial after private approval

- [ ] Review the actual endpoint, access, resource profile, data boundary, retention and zero paid-service budget privately.
- [ ] Run the bounded same-model comparison and report measured results and limitations.
- [ ] Obtain maintainer review before choosing a product inference placement.
