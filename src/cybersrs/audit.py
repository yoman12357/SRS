"""Worker-local private audit context; never write prompts to application logs."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from .repository import Repository

_SINK: ContextVar[Callable[[str, dict], str] | None] = ContextVar("cybersrs_audit", default=None)


@contextmanager
def audit_scope(
    repository: Repository, project_id: str | None, run_id: str | None = None
) -> Iterator[None]:
    """Bind model attempts to one project/run and always clear the worker's context."""
    sink = None
    if project_id is not None:

        def sink(kind: str, payload: dict) -> str:
            """Append private data through the ordinary transactional repository."""
            return repository.record_audit(project_id, kind, payload, run_id)

    token = _SINK.set(sink)
    try:
        yield
    finally:
        _SINK.reset(token)


def record_model_event(kind: str, payload: dict) -> str | None:
    """Persist an inference event only inside an explicit project audit context."""
    sink = _SINK.get()
    return sink(kind, payload) if sink else None
