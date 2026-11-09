"""Pinned Qwen artifacts shared by the provisioner and offline runtime."""

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelProfile:
    """Bind one exact downloadable file to its expected runtime identity."""

    filename: str
    size: int
    sha256: str
    alias: str
    backend: str
    repository: str
    revision: str

    @property
    def url(self) -> str:
        """Construct the publisher URL from the pinned repository and revision."""
        return f"https://huggingface.co/{self.repository}/resolve/{self.revision}/{self.filename}"


QWEN_1_7B = LocalModelProfile(
    filename="Qwen3-1.7B-Q8_0.gguf",
    size=1_834_426_016,
    sha256="061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a",
    alias="soulkiller-qwen3-1.7b",
    backend="local_qwen3_trial",
    repository="Qwen/Qwen3-1.7B-GGUF",
    revision="90862c4b9d2787eaed51d12237eafdfe7c5f6077",
)
QWEN_4B = LocalModelProfile(
    filename="Qwen3-4B-Q4_K_M.gguf",
    size=2_497_280_256,
    sha256="7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5",
    alias="soulkiller-qwen3-4b",
    backend="local_qwen3_4b_trial",
    repository="Qwen/Qwen3-4B-GGUF",
    revision="bc640142c66e1fdd12af0bd68f40445458f3869b",
)
PROFILES = {"qwen3-1.7b": QWEN_1_7B, "qwen3-4b": QWEN_4B}


def main(arguments: list[str]) -> int:
    """Write one trusted tab-separated profile for the shell provisioner."""
    profile = PROFILES.get(arguments[0]) if len(arguments) == 1 else None
    if profile is None:
        print("Select qwen3-1.7b or qwen3-4b.", file=sys.stderr)
        return 2
    print(profile.filename, profile.size, profile.sha256, profile.url, sep="\t")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
