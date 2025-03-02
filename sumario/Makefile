# -*- coding: utf-8; mode: makefile-gmake; -*-

MAKEFLAGS += --no-print-directory --warn-undefined-variables

SHELL := bash
.SHELLFLAGS := -euo pipefail -c

HERE := $(shell cd -P -- $(shell dirname -- $$0) && pwd -P)

export PATH := /root/.local/bin:$(PATH)

.PHONY: all
all: lint test

.PHONY: is-defined-%
is-defined-%:
	@$(if $(value $*),,$(error The environment variable $* is undefined))

IS_IN_CONTAINER ?= 0

define CONTAINER_REQUIRED_MESSAGE

This command must be run *inside* the container. Please use the Makefile in
the top-level directory of this project instead
endef

.PHONY: is-in-container
is-in-container:
ifneq ($(IS_IN_CONTAINER),1)
	@$(if $(shell grep -cs dumb-init /proc/1/cmdline),,$(error $(CONTAINER_REQUIRED_MESSAGE)))
endif

.PHONY: minify-css minify-js
minify-css minify-js: is-in-container
	@$(MAKE) -C src/sumario/static $@

.PHONY: update-deps
update-deps: is-in-container
	@uv lock --upgrade

.PHONY: hash-assets
hash-assets: minify-css minify-js
	@uv run flask --app "sumario.app:create_app()" hash-assets

.PHONY: create-db
create-db: is-in-container
	@uv run flask --app "sumario.app:create_app()" create-db

.PHONY: delete-db
delete-db: is-in-container
	@uv run flask --app "sumario.app:create_app()" delete-db

.PHONY: create-migration
create-migration: is-in-container
	@uv run flask --app "sumario.app:create_app()" db migrate

.PHONY: migrate-db
migrate-db: is-in-container
	@uv run flask --app "sumario.app:create_app()" db upgrade

.PHONY: format
format: is-in-container
	@uv run ruff format .

.PHONY: check-format
check-format: is-in-container
	@uv run ruff format . --check

.PHONY: check-ruff
check-ruff: is-in-container
	@uv run ruff check .

.PHONY: check-bandit
check-bandit: is-in-container
	@uv run bandit -r src/sumario -x tests

.PHONY: check-vulns
check-vulns: is-in-container
	@uv run safety check

.PHONY: lint
lint: check-format check-ruff check-bandit check-vulns

.PHONY: test
test: hash-assets
	@uv run pytest

.PHONY: coverage
coverage: hash-assets
	@uv run pytest --cov=sumario --cov-report=html --cov-report=term

.PHONY: run
run: hash-assets
	@uv run python -m gunicorn -w 4 -b 0.0.0.0:3000 --preload "sumario.app:run()"

.PHONY: shell
shell: is-in-container
	@bash -l || true

.PHONY: create-locale
create-locale: is-defined-LANGUAGE
	@uv run pybabel init -d src/sumario/translations -i src/sumario/messages.pot -l $(LANGUAGE)

.PHONY: extract-messages
extract-messages: is-in-container
	@uv run pybabel extract --no-wrap -F babel.cfg -o src/sumario/messages.pot src/sumario

.PHONY: update-messages
update-messages: is-in-container
	@uv run pybabel update --no-wrap -d src/sumario/translations -i src/sumario/messages.pot

.PHONY: compile-messages
compile-messages: is-in-container
	@uv run pybabel compile -d src/sumario/translations

.PHONY: build-whl
build-whl: hash-assets
	@uv run python -m build -n -w

.PHONY: publish-whl
publish-whl: is-defined-GITLAB_USERNAME is-defined-GITLAB_PASSWORD is-defined-VERSION
	@uv run twine upload dist/sumario-$$VERSION-py3-none-any.whl            \
	    -u $$GITLAB_USERNAME -p $$GITLAB_PASSWORD                           \
	    --repository-url https://gitlab.com/api/v4/projects/48453638/packages/pypi
