# Clued

[![CI](https://github.com/wonnor-pro/clued/actions/workflows/ci.yml/badge.svg)](https://github.com/wonnor-pro/clued/actions/workflows/ci.yml)

> Leave clues for your future debugging self.

`clued` attaches structured, human-readable context to exceptions as they propagate — without changing the exception type, wrapping in a new exception, or parsing strings later.

## Install

Install with pip

```bash
pip install clued
```

or install with uv

```bash
uv add clued
```

Requires Python 3.11+. Zero dependencies.

## The Problem

When an error happens deep in your call stack, you typically get one of two outcomes:

**Option A — bare exception, no context:**

```python
def process_order(order_id):
    user = get_user(order_id)   # raises ValueError("invalid id format")
    charge(user)
```

```text
ValueError: invalid id format
  File "app.py", line 2, in get_user
```

The traceback tells you *where* it happened, not *why*. You don't know which order, which user, or what the system was trying to do at a higher level.

**Option B — verbose try/except wrapping:**

```python
def process_order(order_id):
    try:
        user = get_user(order_id)
    except ValueError as e:
        raise OrderProcessingError(
            f"failed to process order {order_id}: could not fetch user"
        ) from e
```

This works, but it's tedious. Every layer of your call stack needs its own `try/except/raise from` block. Real codebases end up with dozens of custom exception classes and repetitive wrapping code. Most developers just don't bother — and then they're debugging production issues with a `KeyError: 'name'` and no idea which record or request caused it.

**With `clued`:**

```python
from clued import clue

def process_order(order_id: str, user_id: int) -> None:
    with clue("processing order", order_id=order_id, user_id=user_id) as ctx:
        ctx.refine(step="fetch user")
        user = get_user(order_id)

        ctx.refine(step="charge")
        charge(user)
```

```text
ValueError: invalid id format
  File "app.py", line 4, in get_user
- Clue 0: processing order [order_id='BAD', user_id=-1, step='fetch user'] (app.py:8)
```

Clues nest naturally across call boundaries — each layer adds its own note, inner-to-outer:

```python
from clued import clue

def process_order(order_id: str, user_id: int) -> None:
    with clue("processing order", order_id=order_id, user_id=user_id):
        charge_user(order_id, user_id)

def charge_user(order_id: str, user_id: int) -> None:
    with clue("charging user", user_id=user_id) as ctx:
        ctx.refine(step="fetch card")
        card = get_card(user_id)

        ctx.refine(step="apply charge")
        apply_charge(card, order_id)
```

```text
ValueError: invalid card format
  File "app.py", line 4, in get_card
- Clue 0: charging user [user_id=-1, step='fetch card'] (app.py:11)
- Clue 1: processing order [order_id='BAD', user_id=-1] (app.py:5)
```

One `with` block. No custom exception class. No `raise from`. The context travels with the exception automatically.

## Quick Start

```python
from clued import clue, get_clues

with clue("loading config", path=path, env=env) as ctx:
    ctx.refine(section="database")
    load_db_config(path)
```

On any exception raised inside the block, `clued` calls `add_note()` (PEP 678) to attach a formatted string, and stores a structured `ClueRecord` you can query in code:

```python
except Exception as e:
    for record in get_clues(e):
        print(record.msg, dict(record.kv), f"{record.filename}:{record.lineno}")
```

Nested `with clue(...)` blocks each add their own note — outermost last, so the traceback reads inner-to-outer.

## Features

- **Structured kv** — context stored as typed key-value pairs, not just strings
- **Source location** — note includes the exact file and line where `clue()` or `refine()` was called
- **`refine()`** — narrow context in-place as a block progresses (e.g. track loop index, current step)
- **Async-safe** — uses `ContextVar` for per-task isolation; works with `asyncio.gather` and thread pools
- **Zero dependencies** — stdlib only
- **Fully typed** — ships a `py.typed` marker, passes mypy strict and pyright

## API Reference

| Symbol | Description |
| --- | --- |
| `clue(msg, **kv)` | Context manager. Attaches context on any exception raised within the block. Yields a `ClueHandle`. |
| `ClueHandle.refine(msg=None, **kv)` | Update context in-place. `None` values delete a key. |
| `ClueHandle.reset()` | Restore to original message and clear all kv. |
| `clue_on_error(msg_template, **kv)` | Decorator. Formats `msg_template` with bound arguments and wraps the call in `clue()`. Works on async functions too. |
| `ctx(fn, *args, msg, **kv)` | Inline wrapper. Calls `fn(*args)` inside a `clue()` context. |
| `get_clues(exc)` | Returns `list[ClueRecord]` attached to the exception. |
| `get_clue_dict(exc)` | Returns a flat merged `dict` of all kv (inner clues override outer). |
| `current_clues()` | Returns the active `tuple[ClueHandle, ...]` stack for the current context (useful for logging). |

### `ClueRecord`

```python
@dataclass(frozen=True)
class ClueRecord:
    msg: str
    kv: frozenset[tuple[str, Any]]
    filename: str
    lineno: int
```

## Usage Patterns

### Decorator

```python
from clued import clue_on_error, clue_on_error_async

@clue_on_error("processing item {item_id}", source="worker")
def process_item(item_id: str) -> None:
    ...

@clue_on_error_async("fetch user {user_id}")
async def fetch_user(user_id: int) -> dict[str, str]:
    ...
```

### Inline wrapper

```python
from clued import ctx

result = ctx(load_file, path, msg="loading file", path=path)
```

### Tracking progress in a loop

```python
with clue("batch processing", total=len(items)) as ctx:
    for i, item in enumerate(items):
        ctx.refine(index=i, item_id=item["id"])
        process_item(item)
```

If the batch fails at item 42, the exception note shows exactly which item and index.

### Logging integration

```python
import logging
from clued import current_clues

class ClueFilter(logging.Filter):
    def filter(self, record):
        for handle in current_clues():
            record.__dict__.update(handle.kv)
        return True
```

## How It Works

`clued` is built on two Python stdlib primitives:

- **PEP 678 `add_note()`** (Python 3.11+) — the standard way to attach strings to exceptions. Tools like pytest, rich, and IPython already render `__notes__`, so you get readable output for free.
- **`contextvars.ContextVar`** — each asyncio task and thread inherits a copy-on-write context, so nested tasks each carry their own clue stack and cannot interfere with each other.

When an exception exits a `clue` block, two things happen:

1. A formatted string (`- Clue N: msg [k=v] (file:line)`) is appended via `add_note()`, where `N` is the depth index (0 = innermost).
2. A `ClueRecord` is appended to `exc.__clues__` for structured access.

No monkeypatching. No custom exception base class. No runtime overhead on the happy path.

## Development

```bash
# Set up or Sync python environment
make sync

# Ruff formatter
make fmt

# Ruff linter & Mypy static type check
make check

# Pytest
make test
```

## License

MIT
