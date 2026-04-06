# `clued` — Build Plan

## Project Summary

**clued** is a Python library that provides ergonomic error context for
exceptions, built on PEP 678 `add_note()`. It lets developers attach
structured, human-readable context to exceptions without changing the
exception type, using a simple `with clue(...)` context manager.

- **Package name:** `clued`
- **PyPI name:** `clued`
- **Python:** >= 3.11
- **Dependencies:** zero (stdlib only)
- **Core size:** ~200 lines
- **License:** MIT
- **Tooling:** uv (project management, building, publishing)

---

## 1. Repository Structure

```
clued/
├── .github/
│   └── workflows/
│       ├── ci.yml                # test + lint on push/PR
│       └── publish.yml           # build + publish on tag
├── .python-version               # "3.11"
├── .gitignore
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── clued/
│       ├── __init__.py           # public API exports
│       ├── _types.py             # Clue dataclass
│       ├── _core.py              # clue() context manager + ClueHandle
│       ├── _decorator.py         # clue_on_error() decorator
│       ├── _functional.py        # ctx() inline wrapper
│       ├── _extract.py           # get_clues(), get_clue_dict(), current_clues()
│       ├── py.typed              # PEP 561 marker (empty file)
│       └── integrations/
│           ├── __init__.py
│           ├── _sentry.py        # Sentry before_send hook
│           ├── _structlog.py     # structlog processor
│           └── _logging.py       # stdlib logging filter
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_refine.py
│   ├── test_decorator.py
│   ├── test_functional.py
│   ├── test_extract.py
│   ├── test_async.py
│   ├── test_threading.py
│   ├── test_integrations.py
│   └── test_performance.py
└── docs/
    └── examples/
        ├── basic_usage.py
        ├── fastapi_middleware.py
        ├── batch_processing.py
        └── sentry_integration.py
```

Use `src/` layout. All source code lives under `src/clued/`.

---

## 2. Project Initialisation with uv

### Prerequisites

Install uv if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Initialise the project

```bash
# Create a library project with src layout
uv init --lib clued
cd clued
```

This creates the skeleton with `src/clued/`, `.python-version`,
`pyproject.toml`, and `README.md`.

### Set Python version

```bash
echo "3.11" > .python-version
```

### pyproject.toml

Replace the generated `pyproject.toml` with:

```toml
[project]
name = "clued"
version = "0.1.0"
description = "Ergonomic error context for Python exceptions, built on PEP 678 add_note()"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Connor Wang", email = "wonnor.pro@gmail.com" },
]
keywords = ["error", "exception", "context", "debugging", "add_note", "PEP678"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Debuggers",
]

[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/clued"
Repository = "https://github.com/YOUR_USERNAME/clued"
Issues = "https://github.com/YOUR_USERNAME/clued/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clued"]

[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "mypy>=1.0",
    "pyright>=1.1",
    "ruff>=0.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.ruff]
target-version = "py311"
```

### Install dev dependencies

```bash
uv sync
```

This creates the `.venv`, installs the project in editable mode,
and installs all dev dependencies. The `uv.lock` file is generated
automatically — commit it to the repository.

---

## 3. Common uv Commands

| Task                        | Command                                 |
|-----------------------------|-----------------------------------------|
| Install/sync all deps       | `uv sync`                               |
| Add a dev dependency        | `uv add --dev <package>`                |
| Run tests                   | `uv run pytest`                         |
| Run type checker            | `uv run mypy src/clued`                 |
| Run linter                  | `uv run ruff check src/ tests/`         |
| Run formatter               | `uv run ruff format src/ tests/`        |
| Build package               | `uv build`                              |
| Publish to TestPyPI         | `uv publish --publish-url https://test.pypi.org/legacy/` |
| Publish to PyPI             | `uv publish`                            |
| Run a single file           | `uv run python docs/examples/basic_usage.py` |
| Test install from PyPI      | `uv run --with clued --no-project -- python -c "from clued import clue"` |

---

## 4. Module Specifications

### 4.1 `_types.py` — Data Types

Define one frozen dataclass:

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Clue:
    """A single error context entry."""
    msg: str
    kv: dict[str, Any]
    filename: str
    lineno: int
```

This is the structured data stored on exceptions and returned by
`get_clues()`. It is called `Clue` (not `ErrorContext`) to match
the library's branding.


### 4.2 `_core.py` — Context Manager and Handle

This is the heart of the library. Two classes and one function.

**ClueHandle** — the object yielded by `with clue(...) as handle:`.
Must use `__slots__` for minimal memory. Fields:

- `msg: str` — current message (mutable via `refine()`)
- `kv: dict[str, Any]` — current key-value pairs (mutable via `refine()`)
- `_original_msg: str` — for `reset()`
- `_loc: tuple[str, int]` — creation site (filename, lineno)
- `_refine_loc: tuple[str, int] | None` — last `refine()` call site

Methods:

- `refine(msg: str | None = None, **kv)` — update context in-place.
  `None` values delete the key. Capture call site via `sys._getframe(1)`.
- `reset()` — restore to original msg, clear all kv, clear `_refine_loc`.
- `_snapshot() -> tuple[str, dict[str, Any], tuple[str, int]]` — return
  current (msg, kv copy, loc) for note building.

**`clue()` context manager:**

```
@contextmanager
def clue(msg: str, **kv) -> Generator[ClueHandle, None, None]:
```

Implementation steps:
1. Capture caller location: `sys._getframe(1)`, extract
   `(f_code.co_filename, f_lineno)`, then `del frame`.
2. Create `ClueHandle(msg, kv, loc)`.
3. Push handle onto ContextVar stack:
   `token = _clue_stack.set(stack + (handle,))`.
4. `yield handle` inside try/except.
5. On `BaseException`:
   a. Call `handle._snapshot()` to get current state.
   b. Format note string: `clue: {msg} [{k=v, ...}] (file:line)`.
   c. Call `e.add_note(note)`.
   d. Append `Clue(msg, kv, filename, lineno)` to `e.__clues__`
      (create list if not exists via `hasattr` check).
   e. Re-raise.
6. In `finally`: `_clue_stack.reset(token)`.

**ContextVar:**

```python
from contextvars import ContextVar

_clue_stack: ContextVar[tuple[ClueHandle, ...]] = ContextVar(
    'clued_stack', default=()
)
```

This gives each async task and thread its own context stack.

**Note formatting function:**

```python
def _format_note(msg: str, kv: dict[str, Any], loc: tuple[str, int]) -> str:
    note = f"clue: {msg}"
    if kv:
        pairs = ", ".join(f"{k}={v!r}" for k, v in kv.items())
        note += f" [{pairs}]"
    note += f" ({loc[0]}:{loc[1]})"
    return note
```


### 4.3 `_decorator.py` — Function Decorator

```python
def clue_on_error(msg_template: str, **extra_kv):
```

Implementation:
1. Return a decorator that wraps the function.
2. Use `inspect.signature` to bind arguments at call time.
3. Format `msg_template` with bound arguments.
4. Wrap the function body in `with clue(formatted_msg, **extra_kv)`.
5. Detect async functions with `inspect.iscoroutinefunction()` and
   create an async wrapper accordingly.
6. Use `@functools.wraps(fn)` to preserve metadata.


### 4.4 `_functional.py` — Inline Wrapper

```python
def ctx(fn, *args, msg: str, **kv):
```

Implementation:
1. Wrap the call `fn(*args)` inside `with clue(msg, **kv)`.
2. Return the result.
3. For async callables, detect with `inspect.iscoroutinefunction()`
   and `await` accordingly.


### 4.5 `_extract.py` — Extraction Functions

Three functions. All read from `__clues__` attribute — no string parsing.

```python
def get_clues(exc: BaseException) -> list[Clue]:
    """Return structured clue list from exception."""
    return getattr(exc, '__clues__', [])

def get_clue_dict(exc: BaseException) -> dict[str, Any]:
    """Return flat merged kv dict. Inner clues override outer."""
    result = {}
    for c in reversed(get_clues(exc)):  # outer first, inner overrides
        result.update(c.kv)
    return result

def current_clues() -> tuple[ClueHandle, ...]:
    """Return active clue stack from ContextVar. For logging integration."""
    return _clue_stack.get()
```

`current_clues()` imports `_clue_stack` from `_core.py`.


### 4.6 `__init__.py` — Public API

Export exactly these names:

```python
from clued._types import Clue
from clued._core import clue, ClueHandle
from clued._decorator import clue_on_error
from clued._functional import ctx
from clued._extract import get_clues, get_clue_dict, current_clues

__all__ = [
    "clue",
    "ClueHandle",
    "Clue",
    "clue_on_error",
    "ctx",
    "get_clues",
    "get_clue_dict",
    "current_clues",
]
```


### 4.7 `integrations/` — Optional Helpers

These are thin functions, not framework dependencies. They import
nothing outside stdlib + clued. Users copy the pattern or call the
helper.

**`_sentry.py`:**
```python
def sentry_before_send(event, hint):
    """Sentry before_send hook that adds clue context."""
```
Read `hint["exc_info"][1]`, call `get_clue_dict()`, add to
`event["contexts"]["clues"]`.

**`_structlog.py`:**
```python
def clue_processor(logger, method_name, event_dict):
    """structlog processor that adds clue context."""
```
Read `event_dict["exc_info"]`, call `get_clues()`, add list of
dicts to `event_dict["clues"]`.

**`_logging.py`:**
```python
class ClueFilter(logging.Filter):
    """Logging filter that injects current clue context as extra fields."""
```
In `filter()`, call `current_clues()`, merge kv into `record.__dict__`.

---

## 5. Test Specifications

### 5.1 `test_core.py`

- **test_basic_context**: exception inside `with clue("msg")` gets a
  note added. Verify `e.__notes__` contains the formatted note.
- **test_preserves_exception_type**: `ValueError` raised inside
  `with clue(...)` is still `ValueError` when caught.
- **test_nested_contexts**: two nested `with clue(...)` blocks add
  two notes in correct order (inner first, outer second).
- **test_kv_pairs**: `with clue("msg", user_id=5)` formats kv in note.
- **test_no_exception_no_side_effects**: verify no notes added, no
  `__clues__` attribute, when no exception occurs.
- **test_base_exception**: works with `KeyboardInterrupt` and other
  `BaseException` subclasses.
- **test_source_location**: note contains correct filename and line number.
- **test_clues_attribute**: `e.__clues__` is a list of `Clue` dataclasses
  with correct msg, kv, filename, lineno.

### 5.2 `test_refine.py`

- **test_refine_updates_kv**
- **test_refine_merges** — preserves existing keys
- **test_refine_overwrites** — same key gets overwritten
- **test_refine_delete_with_none**
- **test_refine_updates_msg**
- **test_reset**
- **test_refine_in_loop** — error at iteration N shows correct kv

### 5.3 `test_decorator.py`

- **test_basic_decorator**
- **test_template_formatting**
- **test_preserves_function_metadata**
- **test_no_error_no_overhead**
- **test_async_decorator**

### 5.4 `test_functional.py`

- **test_ctx_success**
- **test_ctx_error**
- **test_ctx_async**

### 5.5 `test_extract.py`

- **test_get_clues_empty**
- **test_get_clues_ordered**
- **test_get_clue_dict_merge**
- **test_get_clue_dict_empty**
- **test_current_clues_inside_context**
- **test_current_clues_outside_context**

### 5.6 `test_async.py`

- **test_async_basic**
- **test_async_gather_isolation**
- **test_async_nested_tasks**
- **test_async_sequential_refine**
- **test_async_decorator**

### 5.7 `test_threading.py`

- **test_thread_isolation**
- **test_thread_pool**

### 5.8 `test_integrations.py`

- **test_sentry_hook**
- **test_structlog_processor**
- **test_logging_filter**

### 5.9 `test_performance.py`

- **test_happy_path_overhead** — 100k `with clue():pass` < 1s
- **test_refine_overhead** — 100k `refine()` calls < 0.5s
- **test_error_path** — 10k exceptions with 3 nested clues

---

## 6. CI/CD with GitHub Actions

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync
      - name: Lint
        run: uv run ruff check src/ tests/
      - name: Type check
        run: uv run mypy src/clued
      - name: Test
        run: uv run pytest
```

### `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Install dependencies
        run: uv sync
      - name: Build
        run: uv build
      - name: Publish
        run: uv publish
```

This uses PyPI Trusted Publishing — no API tokens needed in CI.
Set up a Trusted Publisher at pypi.org/manage/account/publishing/
before the first publish.

---

## 7. README.md

The README should include these sections in order:

1. **Tagline**: "Leave clues for your future debugging self."
2. **Install**: `pip install clued` (or `uv add clued`)
3. **The Problem** (before/after code comparison)
4. **Quick Start**: basic `with clue(...)` example with output
5. **Features**: structured kv, source location, refine(), async, zero deps
6. **API Reference**: table of all public functions
7. **Integrations**: Sentry, structlog, FastAPI examples
8. **Performance**: happy path cost, comparison to alternatives
9. **How It Works**: PEP 678 explanation
10. **License**: MIT

---

## 8. Build and Publish Steps

```bash
# 1. Sync environment
uv sync

# 2. Run quality checks
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/clued
uv run pytest

# 3. Build
uv build
# Creates dist/clued-0.1.0-py3-none-any.whl and dist/clued-0.1.0.tar.gz

# 4. Test publish (TestPyPI)
uv publish --publish-url https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN

# 5. Test install from TestPyPI
uv run --with clued --index https://test.pypi.org/simple --no-project \
    -- python -c "from clued import clue; print('OK')"

# 6. Production publish
uv publish --token $PYPI_TOKEN

# 7. Verify from PyPI
uv run --with clued --no-project --refresh-package clued \
    -- python -c "from clued import clue; print('OK')"
```

---

## 9. Design Decisions Reference

These decisions were made during the design phase. Do not deviate from them.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Foundation | PEP 678 `add_note()` | Preserves exception type unlike `raise ... from` |
| Storage | Dual: `__notes__` + `__clues__` | Notes for humans, structured data for code. No string parsing in extraction. |
| Async safety | `ContextVar` | Native per-task isolation for asyncio and threading |
| `refine()` scope | Sequential only | For concurrent fan-out, use per-task `with clue()`. Document this. |
| Source location | `sys._getframe(1)` | ~0.05μs, delete frame ref immediately for GC |
| Min Python | 3.11 | Required for `add_note()` |
| Dependencies | Zero | Stdlib only. Integrations are optional helpers, not imports. |
| Package name | `clued` | Import: `from clued import clue`. API: `with clue("msg"):` |
| Attribute name | `__clues__` | On exception objects. Matches library name. |
| Note prefix | `clue:` | E.g. `clue: processing order [order_id='X'] (file:line)` |
| Tooling | uv | Project management, dependency locking, building, publishing |
| Build backend | hatchling | Standard, well-supported, works with uv |
| CI | GitHub Actions + `astral-sh/setup-uv@v5` | Fast CI with uv caching |
| Publishing | uv publish + Trusted Publishing | No API token secrets needed in CI |
