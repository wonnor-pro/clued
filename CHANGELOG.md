# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Refactored `CodeLocation` and snapshot logic to make the structure cleaner

## [0.1.2] - 2026-04-06

### Fixed

- Fixed the issue that the line number for decorator is not where the function being called

## [0.1.1] - 2026-04-06

### Fixed

- Corrected the example using async decoractor in readme

## [0.1.0] - 2026-04-06

### Added

- `clue()` context manager for attaching structured context to exceptions via PEP 678 `add_note()`
- `ClueHandle.refine()` for narrowing context in-place as a block progresses
- `ClueHandle.reset()` for restoring original message and clearing all kv
- `clue_on_error` / `clue_on_error_async` decorators for annotating functions with formatted context
- `ctx()` inline functional wrapper
- `get_clues()`, `get_clue_dict()`, `current_clues()` for structured access to attached clues
- `ClueRecord` dataclass for typed, structured clue data
- Async-safe via `ContextVar`; works with `asyncio.gather` and thread pools
- Zero dependencies; requires Python 3.11+
- Full type annotations; ships `py.typed`, passes mypy strict and pyright

[Unreleased]: https://github.com/wonnor-pro/clued/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/wonnor-pro/clued/releases/tag/v0.1.0
