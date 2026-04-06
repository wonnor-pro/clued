# clued — AI Agent Build Checklist

Follow these steps in order. Check off each step before proceeding.
If a step fails, fix it before moving to the next step.
All commands use `uv` — do NOT use pip, venv, or virtualenv directly.

---

## Phase 1: Project Scaffolding

- [ ] Verify uv is installed: `uv --version`. If not installed:
  `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Create project: `uv init --lib clued && cd clued`
- [ ] Set Python version: `echo "3.11" > .python-version`
- [ ] Replace the generated `pyproject.toml` with the one from the
  build plan (section 2). Key points:
  - `requires-python = ">=3.11"`
  - `build-system` uses `hatchling`
  - `[dependency-groups] dev` contains pytest, pytest-asyncio,
    mypy, pyright, ruff
  - `[tool.hatch.build.targets.wheel] packages = ["src/clued"]`
- [ ] Create directory structure:
  ```
  mkdir -p src/clued/integrations tests docs/examples
  ```
- [ ] Create `LICENSE` file with MIT license text.
- [ ] Create empty `src/clued/py.typed` file (PEP 561 marker).
- [ ] Create empty `__init__.py` files in `src/clued/`,
  `src/clued/integrations/`, and `tests/`.
- [ ] Sync environment: `uv sync`
- [ ] Verify: `uv run python -c "print('setup OK')"` succeeds.

---

## Phase 2: Core Types

- [ ] Create `src/clued/_types.py`.
- [ ] Define `Clue` as a frozen dataclass with fields:
  `msg: str`, `kv: dict[str, Any]`, `filename: str`, `lineno: int`.
- [ ] Verify: `uv run python -c "from clued._types import Clue; print(Clue(msg='test', kv={}, filename='f.py', lineno=1))"` works.

---

## Phase 3: Core Context Manager

- [ ] Create `src/clued/_core.py`.
- [ ] Define `ContextVar` at module level:
  ```python
  _clue_stack: ContextVar[tuple[ClueHandle, ...]] = ContextVar('clued_stack', default=())
  ```
- [ ] Implement `ClueHandle` class with `__slots__`:
  - Fields: `msg`, `kv`, `_original_msg`, `_loc`, `_refine_loc`
  - `__init__(self, msg: str, kv: dict, loc: tuple[str, int])`
  - `refine(self, msg: str | None = None, **kv)` — updates kv in-place,
    `None` values delete keys, captures call site via `sys._getframe(1)`
  - `reset(self)` — restores original msg, clears kv and `_refine_loc`
  - `_snapshot(self)` — returns `(msg, dict(kv), loc)` tuple
- [ ] Implement `_format_note(msg, kv, loc) -> str`:
  Format: `clue: {msg} [{k=v, ...}] (filename:lineno)`
  Omit `[...]` section if kv is empty.
- [ ] Implement `clue()` context manager:
  1. Capture caller frame: `frame = sys._getframe(1)`,
     extract `(f_code.co_filename, f_lineno)`, then `del frame`
  2. Create `ClueHandle`
  3. Push onto ContextVar stack with `.set()`
  4. `yield handle`
  5. On `BaseException`: snapshot handle, format note, call `e.add_note()`,
     append `Clue` to `e.__clues__` (create list if missing), re-raise
  6. In `finally`: reset ContextVar token
- [ ] Write `tests/test_core.py` with ALL these tests:
  - `test_basic_context` — note added to exception
  - `test_preserves_exception_type` — ValueError stays ValueError
  - `test_nested_contexts` — two notes in correct order
  - `test_kv_pairs` — kv formatted in note
  - `test_no_exception_no_side_effects` — clean when no error
  - `test_base_exception` — works with KeyboardInterrupt
  - `test_source_location` — correct file and line in note
  - `test_clues_attribute` — `__clues__` contains Clue dataclasses
- [ ] Verify: `uv run pytest tests/test_core.py` — all pass.

---

## Phase 4: Refine

- [ ] Write `tests/test_refine.py` with ALL these tests:
  - `test_refine_updates_kv`
  - `test_refine_merges` — preserves existing keys
  - `test_refine_overwrites` — same key gets overwritten
  - `test_refine_delete_with_none`
  - `test_refine_updates_msg`
  - `test_reset`
  - `test_refine_in_loop` — error at iteration N shows correct kv
- [ ] Verify: `uv run pytest tests/test_refine.py` — all pass.

---

## Phase 5: Extraction Functions

- [ ] Create `src/clued/_extract.py`.
- [ ] Implement `get_clues(exc) -> list[Clue]`:
  `return getattr(exc, '__clues__', [])`.
- [ ] Implement `get_clue_dict(exc) -> dict[str, Any]`:
  Iterate `reversed(get_clues(exc))`, merge kv dicts.
  Inner clues override outer.
- [ ] Implement `current_clues() -> tuple[ClueHandle, ...]`:
  Import `_clue_stack` from `_core`, return `_clue_stack.get()`.
- [ ] Write `tests/test_extract.py` with ALL these tests:
  - `test_get_clues_empty`
  - `test_get_clues_ordered`
  - `test_get_clue_dict_merge`
  - `test_get_clue_dict_empty`
  - `test_current_clues_inside_context`
  - `test_current_clues_outside_context`
- [ ] Verify: `uv run pytest tests/test_extract.py` — all pass.

---

## Phase 6: Decorator

- [ ] Create `src/clued/_decorator.py`.
- [ ] Implement `clue_on_error(msg_template: str, **extra_kv)`:
  - Use `inspect.signature` + `bind()` to format template from args
  - Detect async with `inspect.iscoroutinefunction()`
  - Create sync or async wrapper accordingly
  - Use `@functools.wraps(fn)` on wrapper
- [ ] Write `tests/test_decorator.py` with ALL these tests:
  - `test_basic_decorator`
  - `test_template_formatting`
  - `test_preserves_function_metadata`
  - `test_no_error_no_overhead`
  - `test_async_decorator`
- [ ] Verify: `uv run pytest tests/test_decorator.py` — all pass.

---

## Phase 7: Functional Wrapper

- [ ] Create `src/clued/_functional.py`.
- [ ] Implement `ctx(fn, *args, msg: str, **kv)`:
  Wrap `fn(*args)` inside `with clue(msg, **kv)`.
  Handle async callables.
- [ ] Write `tests/test_functional.py` with ALL these tests:
  - `test_ctx_success`
  - `test_ctx_error`
  - `test_ctx_async`
- [ ] Verify: `uv run pytest tests/test_functional.py` — all pass.

---

## Phase 8: Async and Threading Tests

- [ ] Write `tests/test_async.py` with ALL these tests:
  - `test_async_basic` — clue works inside async function
  - `test_async_gather_isolation` — concurrent tasks isolated
  - `test_async_nested_tasks` — child inherits parent context
  - `test_async_sequential_refine` — refine in async for-loop
  - `test_async_decorator` — @clue_on_error on async fn
- [ ] Write `tests/test_threading.py` with ALL these tests:
  - `test_thread_isolation` — thread A clue not on thread B exception
  - `test_thread_pool` — ThreadPoolExecutor tasks isolated
- [ ] Verify: `uv run pytest tests/test_async.py tests/test_threading.py` — all pass.

---

## Phase 9: Public API Exports

- [ ] Update `src/clued/__init__.py` to export:
  ```python
  from clued._types import Clue
  from clued._core import clue, ClueHandle
  from clued._decorator import clue_on_error
  from clued._functional import ctx
  from clued._extract import get_clues, get_clue_dict, current_clues

  __all__ = [
      "clue", "ClueHandle", "Clue",
      "clue_on_error", "ctx",
      "get_clues", "get_clue_dict", "current_clues",
  ]
  ```
- [ ] Verify: `uv run python -c "from clued import clue, get_clues, Clue, clue_on_error, ctx, get_clue_dict, current_clues, ClueHandle"` works.
- [ ] Verify: `uv run pytest` — ALL tests pass.

---

## Phase 10: Integrations

- [ ] Create `src/clued/integrations/_sentry.py`:
  ```python
  def sentry_before_send(event, hint):
  ```
  Reads `hint["exc_info"][1]`, calls `get_clue_dict()`, adds to
  `event["contexts"]["clues"]`. Returns event.

- [ ] Create `src/clued/integrations/_structlog.py`:
  ```python
  def clue_processor(logger, method_name, event_dict):
  ```
  Reads `event_dict["exc_info"]`, calls `get_clues()`, adds list
  of dicts to `event_dict["clues"]`. Returns event_dict.

- [ ] Create `src/clued/integrations/_logging.py`:
  ```python
  class ClueFilter(logging.Filter):
  ```
  In `filter()`, calls `current_clues()`, merges kv into record.

- [ ] Update `src/clued/integrations/__init__.py` to export these.

- [ ] Write `tests/test_integrations.py` with tests:
  - `test_sentry_hook` — mock event/hint, verify output
  - `test_structlog_processor` — mock event_dict, verify output
  - `test_logging_filter` — verify kv injected into LogRecord

- [ ] Verify: `uv run pytest tests/test_integrations.py` — all pass.

---

## Phase 11: Performance Tests

- [ ] Write `tests/test_performance.py`:
  - `test_happy_path_overhead` — 100k `with clue():pass` in < 1s
  - `test_refine_overhead` — 100k `refine()` calls in < 0.5s
  - `test_error_path` — 10k exceptions with 3 nested clues
- [ ] Verify: `uv run pytest tests/test_performance.py` — all pass.

---

## Phase 12: Examples

- [ ] Create `docs/examples/basic_usage.py`:
  Basic `with clue(...)` with nested contexts, show traceback output.

- [ ] Create `docs/examples/batch_processing.py`:
  Loop with `refine()`, show the performance-friendly pattern.

- [ ] Create `docs/examples/fastapi_middleware.py`:
  FastAPI middleware using `with clue(...)` to add request context.

- [ ] Create `docs/examples/sentry_integration.py`:
  Sentry setup with `sentry_before_send` hook.

- [ ] Verify: each example runs without errors (mock external deps):
  `uv run python docs/examples/basic_usage.py`

---

## Phase 13: Documentation

- [ ] Write `README.md` with these sections in order:
  1. Tagline: "Leave clues for your future debugging self."
  2. Install: `pip install clued` or `uv add clued`
  3. The Problem — before/after comparison
  4. Quick Start — basic example with output
  5. Features list (structured kv, source location, refine, async, zero deps)
  6. API Reference table
  7. Integrations (Sentry, structlog, FastAPI)
  8. Performance notes
  9. How It Works (PEP 678 explanation)
  10. License
- [ ] Verify: README renders correctly as markdown.

---

## Phase 14: Quality Checks

- [ ] Run full test suite: `uv run pytest` — all pass.
- [ ] Run type checker: `uv run mypy src/clued --strict` — no errors.
- [ ] Run linter: `uv run ruff check src/ tests/` — no errors.
- [ ] Run formatter: `uv run ruff format src/ tests/`.
- [ ] Verify `py.typed` exists at `src/clued/py.typed`.
- [ ] Verify `__all__` in `__init__.py` matches actual exports.
- [ ] Verify no external dependencies in core code (only stdlib imports).
- [ ] Verify `uv.lock` is present and committed.

---

## Phase 15: CI/CD Setup

- [ ] Create `.github/workflows/ci.yml` (see build plan section 6).
  Must use `astral-sh/setup-uv@v5` and run:
  `uv sync`, `uv run ruff check`, `uv run mypy`, `uv run pytest`.
  Matrix test on Python 3.11, 3.12, 3.13.

- [ ] Create `.github/workflows/publish.yml` (see build plan section 6).
  Triggers on `v*` tags. Uses Trusted Publishing with
  `permissions: id-token: write`. Runs `uv build` then `uv publish`.

- [ ] Verify: CI workflow YAML is valid.

---

## Phase 16: Build and Publish

- [ ] Build package: `uv build`
- [ ] Verify dist contains:
  - `dist/clued-0.1.0-py3-none-any.whl`
  - `dist/clued-0.1.0.tar.gz`
- [ ] Test install from built wheel in isolated env:
  ```bash
  uv run --with ./dist/clued-0.1.0-py3-none-any.whl --no-project \
      -- python -c "from clued import clue; print('OK')"
  ```
- [ ] Upload to TestPyPI:
  ```bash
  uv publish --publish-url https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN
  ```
- [ ] Test install from TestPyPI:
  ```bash
  uv run --with clued --index https://test.pypi.org/simple --no-project \
      -- python -c "from clued import clue; print('OK')"
  ```
- [ ] Upload to PyPI:
  ```bash
  uv publish --token $PYPI_TOKEN
  ```
- [ ] Verify from PyPI:
  ```bash
  uv run --with clued --no-project --refresh-package clued \
      -- python -c "from clued import clue; print('OK')"
  ```

---

## Validation Criteria

The project is COMPLETE when ALL of these are true:

1. `pip install clued` (or `uv add clued`) works from PyPI
2. `from clued import clue, get_clues` works
3. `with clue("msg", key="val"):` adds a note on exception
4. Exception type is preserved (not wrapped)
5. `get_clues(exc)` returns structured `Clue` objects without parsing
6. `refine()` works in loops without per-iteration context manager cost
7. Async tasks via `asyncio.gather` have isolated contexts
8. Threads have isolated contexts
9. Source file and line appear in note output
10. All tests pass: `uv run pytest`
11. Type checks pass: `uv run mypy src/clued --strict`
12. Zero external dependencies
13. `uv.lock` is committed
14. CI/CD workflows are present and valid
