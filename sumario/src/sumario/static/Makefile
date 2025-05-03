# -*- coding: utf-8; mode: makefile-gmake; -*-

MAKEFLAGS += --warn-undefined-variables

SHELL := bash
.SHELLFLAGS := -euo pipefail -c

HERE := $(shell cd -P -- $(shell dirname -- $$0) && pwd -P)

.PHONY: all
all: minify-css minify-js

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

MIN_CSS = $(subst src/,build/,$(patsubst %.css,%.min.css,$(wildcard src/**/*.css)))

build/css/%.min.css: src/css/%.css
	@minify $< > $@

.PHONY: minify-css
minify-css: is-in-container $(MIN_CSS)

MIN_JS = $(subst src/,build/,$(patsubst %.js,%.min.js,$(wildcard src/**/*.js)))

build/js/%.min.js: src/js/%.js
	@minify $< > $@

.PHONY: minify-js
minify-js: is-in-container $(MIN_JS)
