# -*- coding: utf-8; mode: makefile-gmake; -*-

MAKEFLAGS += --warn-undefined-variables

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

.install-deps: pyproject.toml
	@python3 -m pip install --user -e ".[builder]" && touch .install-deps

.PHONY: install-deps
install-deps: is-in-container .install-deps

.PHONY: check-deps
check-deps: install-deps
	@python3 -m pip list -o

.PHONY: update-deps
update-deps: install-deps
	@echo TODO:

.PHONY: hash-assets
hash-assets: minify-css minify-js install-deps
	@flask --app "sumario.app:create_app()" hash-assets

.PHONY: create-db
create-db: install-deps
	@flask --app "sumario.app:create_app()" create-db

.PHONY: delete-db
delete-db: install-deps
	@flask --app "sumario.app:create_app()" delete-db

.PHONY: create-migration
create-migration: install-deps
	@flask --app "sumario.app:create_app()" db migrate

.PHONY: migrate-db
migrate-db: install-deps
	@flask --app "sumario.app:create_app()" db upgrade

.PHONY: format
format: install-deps
	@ruff format .

.PHONY: check-format
check-format: install-deps
	@ruff format . --check

.PHONY: check-style
check-style: install-deps
	@ruff check .

.PHONY: check-quality
check-quality: install-deps
	@bandit -r src/sumario -x tests

.PHONY: check-vulnerabilities
check-vulnerabilities: install-deps
	@safety check

.PHONY: lint
lint: check-format check-style check-quality check-vulnerabilities

.PHONY: test
test: hash-assets
	@pytest

.PHONY: coverage
coverage: hash-assets
	@pytest --cov=sumario --cov-report=html --cov-report=term

.PHONY: run
run: hash-assets
	@python3 -m gunicorn -w 4 -b 0.0.0.0:3000 --preload "sumario.app:run()"

.PHONY: shell
shell: is-in-container
	@bash -l || true

.PHONY: watch
watch: is-in-container
	@modd -f modd.sumario.conf

.PHONY: create-locale
create-locale: is-defined-LANGUAGE install-deps
	@pybabel init -d src/sumario/translations -i src/sumario/messages.pot -l $(LANGUAGE)

.PHONY: extract-messages
extract-messages: install-deps
	@pybabel extract --no-wrap -F babel.cfg -o src/sumario/messages.pot src/sumario

.PHONY: update-messages
update-messages: install-deps
	@pybabel update --no-wrap -d src/sumario/translations -i src/sumario/messages.pot

.PHONY: compile-messages
compile-messages: install-deps
	@pybabel compile -d src/sumario/translations

.PHONY: build-whl
build-whl: hash-assets
	@python3 -m build -n -w

.PHONY: publish-whl
publish-whl: is-defined-GITLAB_USERNAME is-defined-GITLAB_PASSWORD is-defined-VERSION install-deps
	@twine upload dist/sumario-$$VERSION-py3-none-any.whl                   \
	    -u $$GITLAB_USERNAME -p $$GITLAB_PASSWORD                           \
	    --repository-url https://gitlab.com/api/v4/projects/48453638/packages/pypi
