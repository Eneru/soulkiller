"""Typed completion collaborators keep process ownership format independent."""

from collections.abc import Callable

from .worker_outcome import WorkerOutcome

type CompletionClassifier[T] = Callable[[int | None, WorkerOutcome | None, bytes, str], T]
