# Python in the devcontainer editor

Rebuild/reopen Soulkiller in **VS Code 1.110 or newer**. The devcontainer installs
these versioned extensions on the container side, alongside the existing Hadolint
extension; the Docker CLI image alone does not install or run VS Code extensions.

| Extension | Version | Role |
| --- | --- | --- |
| `ms-python.python` | 2026.6.0 | Interpreter selection and pytest Test Explorer |
| `ms-python.vscode-pylance` | 2026.4.1 | Completion and source navigation |
| `ms-python.debugpy` | 2026.6.0 | Python extension's debugger companion |
| `ms-python.vscode-python-envs` | 1.38.0 | Python extension's environment companion |
| `charliermarsh.ruff` | 2026.84.0 | Native lint diagnostics and explicit formatting |
| `ms-python.mypy-type-checker` | 2026.6.0 | Strict type diagnostics |

The Python extension includes the three companion extensions in its extension
pack; listing their versions explicitly avoids leaving those additions unversioned.
Update these pins, their editor compatibility and settings together in a reviewed PR.
The versions describe installation requests; inspect the actual installed versions
if an existing editor profile has other versions or automatic extension updates.

## Interpreter and diagnostics

The [container settings](../.devcontainer/devcontainer.json) select
`/opt/python-tools/bin/python`, the image's isolated CPython 3.13.16 tool environment.
If VS Code already remembers a different interpreter, **Python: Select Interpreter**
then **Enter interpreter path** and select that path: `defaultInterpreterPath` does
not replace a previous workspace selection. Check the container status indicator
and **Developer: Show Running Extensions** to confirm remote execution.

Ruff uses `/opt/python-tools/bin/ruff` and its native server; it discovers the
nearest `pyproject.toml`, with filesystem configuration taking precedence. Mypy uses
`/opt/python-tools/bin/mypy`, `importStrategy=fromEnvironment` and the same image
interpreter, with the experiment as
its working directory, its explicit `pyproject.toml`, and a container `/tmp` cache.
Its `custom` scope checks the configured `src` and `tests`; external-binary mode
checks saved files. The environment import strategy also prevents the extension
from injecting bundled mypy modules into the external binary. Save before
expecting fresh mypy diagnostics. Pylance includes
the experiment's `src` for navigation; its type-checking mode is off so strict mypy
remains the type policy. Use **Format Document** or explicit Ruff code actions;
format-on-save is disabled. Shell auto-activation is disabled because the image
already places the tools on PATH; no environment creation or package installation
is needed. `rich` is a transitive tool-display dependency, not an editor extension.

Inspect **Output → Ruff**, **Mypy Type Checker** and **Python** when diagnostics or
tests are missing. A missing image tool is a setup error, not a reason to install a
different host or bundled version. Run **Dev Containers: Rebuild Container** to
apply configuration changes.

## Test Explorer and full checks

The Python extension enables pytest and disables unittest, sets the working
directory to `experiments/text-pdf`, and discovers `tests` with pytest's cache
provider disabled. The image's pytest and the experiment's configured `pythonpath`
are used without an editable package install. Use **Testing → Refresh Tests**, then
run a test or the current suite. The corpus-input tranche expands the synthetic cases;
use python -m pytest --collect-only from experiments/text-pdf to see the count.

Test Explorer runs are useful feedback, but do not enforce the 70% coverage floor,
Bandit, secrets or advisory checks. Run the checked-in **Tasks: Run Task →
Soulkiller: Python static/tests/audit/all**, or the [canonical CLI](quality-checks.md),
for those gates. Advisory audits explicitly need network access; static analysis
and tests do not. Debugging via the companion extension is available for manual
use, but has not been validated by the foundation's CLI tests.

## Verify the integration

In the rebuilt container, confirm the interpreter path/version and run
`bash tools/checks/python.sh static` and `bash tools/checks/python.sh tests`.
In VS Code, inspect the installed remote extension versions, refresh the current synthetic tests,
open a source file and navigate to an imported definition. Temporarily introduce
an unused import and, separately, an incompatible annotated assignment in an
uncommitted synthetic file in the experiment; save and confirm Ruff/mypy diagnostics,
then remove only that probe. Do not commit the intentionally invalid file.

Record these manual UI results separately from extension-manifest, backend or CLI
validation. Successful container checks alone do not prove VS Code activation,
Problems rendering, navigation, test discovery or debugging worked in the UI.

Official references: [Python testing](https://code.visualstudio.com/docs/python/testing),
[interpreter settings](https://code.visualstudio.com/docs/python/settings-reference),
[Ruff settings](https://docs.astral.sh/ruff/editors/settings/),
[versioned mypy extension](https://github.com/microsoft/vscode-mypy/tree/v2026.6.0).
