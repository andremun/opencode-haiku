# opencode-haiku: checks, inputs and the release archive.
# Build steps need the pinned caches (make fetch) and guest-built native parts (docs/BUILD.md).
VERSION := $(shell cat VERSION)
HAIKU_K40C_ROOT ?= ../haiku-k40c
PY_FILES := $(shell git ls-files '*.py')
SH_FILES := $(shell git ls-files '*.sh' src/opencode)

.PHONY: help check lint test fetch dist stage clean
help:
	@echo "make check   unit tests, lint, shell syntax, secret scan (no VM, no network)"
	@echo "make fetch   download and check the pinned upstream inputs (reference/INPUTS.json)"
	@echo "make dist    build the release archive $(VERSION) into dist/ (needs caches and native parts)"
	@echo "make stage   stage the archive and source for the persistent VM (tests/acceptance/vm)"
	@echo "make clean   remove dist/"

check: lint test
	python3 tools/secrets/scan_secrets.py

lint:
	ruff check --select E9,F63,F7,F82 $(PY_FILES)
	for f in $(SH_FILES); do sh -n "$$f" || exit 1; done
	for f in $$(git ls-files '*.mjs' '*.cjs'); do node --check "$$f" || exit 1; done

test:
	HAIKU_K40C_ROOT=$(HAIKU_K40C_ROOT) python3 tests/unit/test_review_runners.py
	HAIKU_K40C_ROOT=$(HAIKU_K40C_ROOT) python3 tests/unit/test_t7610_runners.py
	python3 tests/unit/install-test.py

fetch:
	python3 build/fetch.py

dist:
	sh build/build_bundle.sh
	mkdir -p dist
	cp share/opencode-haiku-tui-$(VERSION).tar.gz dist/
	cp results/opencode-tui-package.json dist/MANIFEST.json
	cd dist && sha256sum opencode-haiku-tui-$(VERSION).tar.gz > SHA256SUMS

stage:
	python3 tests/acceptance/vm/stage_t7610.py

clean:
	rm -rf dist
