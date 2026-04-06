ROOT_DIR=$(CURDIR)
RUN=uv run

.PHONY: sync
sync:
	uv sync

.PHONY: fmt
fmt:
	$(RUN) ruff check --select I --fix $(ROOT_DIR)
	$(RUN) ruff format $(ROOT_DIR)

.PHONY: test
test:
	$(RUN) pytest $(ROOT_DIR)/tests

.PHONY: lint
lint:
	$(RUN) ruff check $(ROOT_DIR)

.PHONY: check-types
check-types:
	$(RUN) mypy $(ROOT_DIR)

.PHONY: check
check: lint check-types
