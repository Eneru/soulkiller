# Experimental Python toolchain

Python is installed for the reviewed extraction evaluation only; this does not
select Soulkiller's application language or Windows distribution strategy.

[Native editor setup](python-editor.md) pins VS Code integrations separately
from these runtime packages. `rich` is a transitive display dependency; it has no
editor extension to install.

## Provisioning and artifacts

CPython 3.13.16 is compiled without PGO/LTO, with at most two compiler jobs, from
[the official source release](https://www.python.org/downloads/release/python-31316/)
on the same pinned Ubuntu 24.04 base as the final image. XZ source SHA-256:
f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d.

The runtime lives in /opt/python and tools in /opt/python-tools; Ubuntu's system
Python is unchanged. Shared runtime libraries and direct APT build dependencies
are pinned in the Dockerfile; build-only compilers/headers stay in builder stages.
This is a minimal runtime for evaluation tooling, not every optional stdlib module.
APT transitives remain mirror-resolved; no bit-for-bit reproducibility is claimed.

The [direct tool pins](../.devcontainer/python/requirements.in) and complete
[wheel hash lock](../.devcontainer/python/requirements.lock) were resolved with
CPython 3.13.16 in the devcontainer. Hashes cover pure wheels and the published
CPython 3.13 Linux amd64/arm64 wheel artifacts where applicable. Builds force
wheel-only hash checking from PyPI; no source-package build scripts.
ARM64 hashes are provisioning intent, not execution evidence.
[Secure pip installation](https://pip.pypa.io/en/stable/topics/secure-installs/).

## Dependency terms and inventory

Tool snapshot: 2026-10-05; pypdf addition checked 2026-10-11. The table records
declared upstream package terms, with links to the exact version metadata. It is not a legal interpretation. Distribution
license files remain installed under /opt/python-tools/lib/python3.13/site-packages
(in dist-info or package license directories). CPython's source license is retained
in /opt/python/share/licenses/CPython/LICENSE, with its stdlib notices.
Existing Ubuntu/base-image dependencies retain their distribution notices.
This document and third-party notices do not modify Soulkiller's LICENSE.
Pip's vendored libraries are part of its distribution and retained notices;
pip-audit package advisories are not a complete OS/interpreter/vendored-code audit.

| Package | Version | Declared terms |
| --- | --- | --- |
| [ast_serialize](https://pypi.org/project/ast_serialize/0.12.1/) | 0.12.1 | MIT |
| [bandit](https://pypi.org/project/bandit/1.9.4/) | 1.9.4 | Apache-2.0 |
| [boolean.py](https://pypi.org/project/boolean.py/5.0/) | 5.0 | BSD-2-Clause |
| [CacheControl](https://pypi.org/project/CacheControl/0.14.4/) | 0.14.4 | Apache-2.0 |
| [certifi](https://pypi.org/project/certifi/2026.7.22/) | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0) |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/3.5.2/) | 3.5.2 | MIT |
| [coverage](https://pypi.org/project/coverage/7.16.2/) | 7.16.2 | Apache-2.0 |
| [cyclonedx-python-lib](https://pypi.org/project/cyclonedx-python-lib/11.12.0/) | 11.12.0 | Apache Software License |
| [defusedxml](https://pypi.org/project/defusedxml/0.7.1/) | 0.7.1 | Python Software Foundation License |
| [filelock](https://pypi.org/project/filelock/4.0.12/) | 4.0.12 | MIT |
| [idna](https://pypi.org/project/idna/3.20/) | 3.20 | BSD-3-Clause |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.0/) | 2.3.0 | MIT |
| [librt](https://pypi.org/project/librt/0.16.0/) | 0.16.0 | MIT |
| [license-expression](https://pypi.org/project/license-expression/30.4.4/) | 30.4.4 | Apache-2.0; bundled license data CC-BY-4.0 |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | 4.2.0 | MIT License |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | MIT License |
| [msgpack](https://pypi.org/project/msgpack/1.2.3/) | 1.2.3 | Apache-2.0 |
| [mypy](https://pypi.org/project/mypy/2.4.0/) | 2.4.0 | MIT |
| [mypy_extensions](https://pypi.org/project/mypy_extensions/1.1.0/) | 1.1.0 | MIT |
| [packageurl-python](https://pypi.org/project/packageurl-python/0.17.6/) | 0.17.6 | MIT License |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [pathspec](https://pypi.org/project/pathspec/1.1.1/) | 1.1.1 | Mozilla Public License 2.0 (MPL 2.0) |
| [pip](https://pypi.org/project/pip/26.2.1/) | 26.2.1 | MIT |
| [pip_api](https://pypi.org/project/pip_api/0.0.35/) | 0.0.35 | Apache Software License |
| [pip_audit](https://pypi.org/project/pip_audit/2.10.1/) | 2.10.1 | Apache Software License |
| [pip-requirements-parser](https://pypi.org/project/pip-requirements-parser/32.0.1/) | 32.0.1 | MIT |
| [platformdirs](https://pypi.org/project/platformdirs/4.12.3/) | 4.12.3 | MIT |
| [pluggy](https://pypi.org/project/pluggy/1.6.0/) | 1.6.0 | MIT License |
| [py-serializable](https://pypi.org/project/py-serializable/2.1.0/) | 2.1.0 | Apache Software License |
| [Pygments](https://pypi.org/project/Pygments/2.21.0/) | 2.21.0 | BSD-2-Clause |
| [pyparsing](https://pypi.org/project/pyparsing/3.3.3/) | 3.3.3 | MIT |
| [pypdf](https://pypi.org/project/pypdf/6.20.0/) | 6.20.0 | BSD-3-Clause |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | MIT |
| [PyYAML](https://pypi.org/project/PyYAML/6.0.3/) | 6.0.3 | MIT License |
| [requests](https://pypi.org/project/requests/2.34.2/) | 2.34.2 | Apache Software License |
| [rich](https://pypi.org/project/rich/15.0.0/) | 15.0.0 | MIT License |
| [ruff](https://pypi.org/project/ruff/0.16.10/) | 0.16.10 | MIT |
| [sortedcontainers](https://pypi.org/project/sortedcontainers/2.4.0/) | 2.4.0 | Apache Software License |
| [stevedore](https://pypi.org/project/stevedore/5.9.1/) | 5.9.1 | Apache-2.0 |
| [tomli](https://pypi.org/project/tomli/2.4.1/) | 2.4.1 | MIT |
| [tomli_w](https://pypi.org/project/tomli_w/1.2.0/) | 1.2.0 | MIT License |
| [typing_extensions](https://pypi.org/project/typing_extensions/4.16.0/) | 4.16.0 | PSF-2.0 |
| [urllib3](https://pypi.org/project/urllib3/2.8.0/) | 2.8.0 | MIT |

## Native PDF candidate

The [pypdf adapter tranche](../openspec/changes/implement-pypdf-adapter/design.md)
adds base `pypdf==6.20.0` to the same image environment. The reviewed evaluation
snapshot proposed 6.19.0; the [6.20.0 upstream release](https://github.com/py-pdf/pypdf/releases/tag/6.20.0)
adds per-stream filter-count and accumulated-decoding-work guards. This small
version update does not adopt a production parser or make parsing a sandbox.

The verified `pypdf-6.20.0-py3-none-any.whl` SHA-256 is
`f003fc2014814d264fe7dd3f9d435c158e23e1a85a2233f87a0a2d6d21c914ad`;
[PyPI release metadata](https://pypi.org/project/pypdf/6.20.0/#files) publishes the
same hash. The [tagged dependency metadata](https://github.com/py-pdf/pypdf/blob/6.20.0/pyproject.toml)
requires Python >=3.9 and only conditionally requires `typing_extensions` below
Python 3.11. Base pypdf adds no transitive package on CPython 3.13.16; all existing
tool pins and hashes are preserved. No crypto, image, font, Brotli, model or other
optional extras are requested.

The wheel includes `pypdf/py.typed` and
`pypdf-6.20.0.dist-info/licenses/LICENSE`. Image installation retains the BSD-3-Clause
notice under `/opt/python-tools/lib/python3.13/site-packages/`; Soulkiller's root
LICENSE is unchanged. Rebuild the devcontainer to install the new locked candidate;
no separate user-level pip command is needed. See [editor setup](python-editor.md)
for import/type navigation and CLI verification.

## Update procedure

1. In the devcontainer, review primary releases/advisories and change exact
   direct requirements. Never update global host configuration.
2. Resolve the full graph with the intended interpreter and a clean venv using
   pip's dry-run installation report, wheel-only PyPI downloads and
   ignore-installed. Inspect every transitive dependency.
3. Freeze every resolved version and SHA-256 in requirements.lock. Check the
   downloaded artifact hash against exact upstream release metadata; include
   intended Linux architecture wheels and reject unexpected source/model extras.
4. Update this inventory and image source/library pins as needed, rebuild, run
   static/tests/audit plus the canonical foundation checks and request review.

Keep temporary reports/wheels container-local; no real corpus or secrets.
The bootstrap pip comes from the verified CPython ensurepip bundle and is pinned
again by the complete tool lock. Final image installs are root-owned, and routine
checks run as ubuntu without global/user package installation.

## Gates

See [quality commands](quality-checks.md#experimental-python-checks) and
[the experiment](../experiments/text-pdf/README.md). pytest 9.1.1, coverage 7.16.2,
Ruff 0.16.10, mypy 2.4.0, Bandit 1.9.4 and pip-audit 2.10.1 are direct tool pins.
Advisory scans send public package metadata only, require no account, and fail
on findings/tool/feed errors. Report actual results with their date; neither
a hash lock nor a clean audit proves absence of future vulnerabilities.
[pip-audit](https://github.com/pypa/pip-audit).
