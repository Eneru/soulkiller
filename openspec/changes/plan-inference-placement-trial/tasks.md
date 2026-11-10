## Review

- [x] Confirm PR #33 merge and use its 4B results to select a comparison control.
- [x] Prepare the scope, data boundary, acceptance criteria and stop conditions.
- [ ] Obtain maintainer approval of the implementation scope.

## Transport implementation after approval

- [ ] Add the explicit synthetic-only client/worker transport and verify local mode compatibility.
- [ ] Cover no-call paths, identity and protocol failures, limits, local citation validation and cleanup using synthetic doubles and a container-local integration test.
- [ ] Validate new dependencies and editor/CLI/CI checks in the devcontainer, without real endpoint access, credentials or paid requests.
- [ ] Deliver a short manual synthetic-worker walkthrough and obtain maintainer review.

## Separate live trial after private approval

- [ ] Review the actual endpoint, access, resource profile, data boundary, retention and zero paid-service budget privately.
- [ ] Run the bounded same-model comparison and report measured results and limitations.
- [ ] Obtain maintainer review before choosing a product inference placement.
