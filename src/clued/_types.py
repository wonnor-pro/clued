from dataclasses import dataclass
from typing import Any, NamedTuple, final


@final
class CodeLocation(NamedTuple):
    filename: str
    lineno: int

    @property
    def path(self) -> str:
        return f"{self.filename}:{self.lineno}"


@dataclass(frozen=True)
class ClueRecord:
    msg: str
    kv: frozenset[tuple[str, Any]]
    loc: CodeLocation

    def format_note(self, depth: int) -> str:
        return f"- {depth}: {self.msg} [{', '.join(f'{k}={v!r}' for k, v in self.kv)}] ({self.loc.path})"
