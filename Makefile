# -*- coding: utf-8; mode: makefile-gmake; -*-

MAKEFLAGS += --warn-undefined-variables

SHELL := bash
.SHELLFLAGS := -euo pipefail -c

HERE := $(shell cd -P -- $(shell dirname -- $$0) && pwd -P)

CONTAINER_REGISTRY := registry.gitlab.com

GIT_COMMIT_HASH := $(shell git rev-parse HEAD)
GIT_BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD)

BUILDER_IMAGE := $(CONTAINER_REGISTRY)/jstvsolutions/sumario/builder:$(GIT_BRANCH_NAME)
RELEASE_IMAGE := $(CONTAINER_REGISTRY)/jstvsolutions/sumario/release:$(GIT_COMMIT_HASH)

# https://github.com/pypa/setuptools/issues/3772#issuecomment-1384342813
VERSION := "0.1+$(GIT_COMMIT_HASH)"
export VERSION

.PHONY: all
all: sumario/lint sumario/coverage

.PHONY: has-command-%
has-command-%:
	@$(if $(shell command -v $* 2> /dev/null),,$(error The command $* does not exist in PATH))

.PHONY: is-defined-%
is-defined-%:
	@$(if $(value $*),,$(error The environment variable $* is undefined))

.PHONY: is-repo-clean
is-repo-clean: has-command-git
	@git diff-index --quiet HEAD --

.PHONY: container/login
container/login: is-defined-GITLAB_USERNAME is-defined-GITLAB_PASSWORD is-defined-CONTAINER_REGISTRY has-command-docker
	@echo $$GITLAB_PASSWORD | docker login --username $$GITLAB_USERNAME --password-stdin $(CONTAINER_REGISTRY)

.PHONY: container/create-network-%
container/create-network-%: has-command-docker
	@docker network create --driver bridge $* || true

.PHONY: contaier/build-builder
container/build-builder: is-defined-BUILDER_IMAGE has-command-docker container/create-network-sumario
	@docker build --pull -f Containerfile.builder -t $(BUILDER_IMAGE) .

.PHONY: container/run-builder
container/run-builder: container/build-builder
	@docker run --network sumario --rm                                      \
	    --name sumario.internal                                             \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$(openssl rand -hex 16)                              \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -p 3000:3000                                                        \
	    $(BUILDER_IMAGE)                                                    \
	    make run

.PHONY: sumario/build-whl
sumario/build-whl: is-repo-clean container/build-builder
	@docker run --rm                                                        \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$(openssl rand -hex 16)                              \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -v $(HERE)/sumario:/mnt/workdir                                     \
	    -v sumario-backend-deps:/root/.local                                \
            $(BUILDER_IMAGE)                                                    \
	    make build-whl

.PHONY: sumario/publish-whl
sumario/publish-whl: container/build-builder
	@docker run --rm                                                        \
	    -e GITLAB_USERNAME=$$GITLAB_USERNAME                                \
	    -e GITLAB_PASSWORD=$$GITLAB_PASSWORD                                \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$(openssl rand -hex 16)                              \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -v sumario-backend-deps:/root/.local                                \
	    -v $(HERE)/sumario:/mnt/workdir                                     \
            $(BUILDER_IMAGE)                                                    \
	    make publish-whl

.PHONY: container/build-release
container/build-release: is-defined-RELEASE_IMAGE has-command-docker
	@docker build --pull -f Containerfile.release -t $(RELEASE_IMAGE) .     \
	    --build-arg GITLAB_USERNAME=$$GITLAB_USERNAME                       \
	    --build-arg GITLAB_PASSWORD=$$GITLAB_PASSWORD                       \
	    --build-arg VERSION=$(VERSION)

.PHONY: container/run-release
container/run-release: container/build-release
	@docker run --network sumario --rm                                      \
	    --name sumario.internal                                             \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$(openssl rand -hex 16)                              \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -p 3000:3000                                                        \
	    $(RELEASE_IMAGE)

.PHONY: container/push-release
container/push-release: is-defined-RELEASE_IMAGE has-command-docker container/login
	@docker push $(RELEASE_IMAGE)

.PHONY: container/pull-release
container/pull-release: is-defined-RELEASE_IMAGE has-command-docker container/login
	@docker pull -q $(RELEASE_IMAGE)

.PHONY: sumario/%
sumario/%: is-defined-GITLAB_USERNAME is-defined-GITLAB_PASSWORD is-defined-POSTGRES_HOSTNAME is-defined-POSTGRES_TCP_PORT is-defined-POSTGRES_USERNAME is-defined-POSTGRES_PASSWORD is-defined-SECRET_KEY container/build-builder
	@docker run --network sumario --rm                                      \
	    --name sumario.internal                                             \
	    -e GITLAB_USERNAME=$$GITLAB_USERNAME                                \
	    -e GITLAB_PASSWORD=$$GITLAB_PASSWORD                                \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$SECRET_KEY                                          \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -v sumario-backend-deps:/root/.local                                \
	    -v $(HERE)/sumario:/mnt/workdir                                     \
            $(BUILDER_IMAGE)                                                    \
	    make $*

.PHONY: sumario/shell
sumario/shell: is-defined-GITLAB_USERNAME is-defined-GITLAB_PASSWORD is-defined-POSTGRES_HOSTNAME is-defined-POSTGRES_TCP_PORT is-defined-POSTGRES_USERNAME is-defined-POSTGRES_PASSWORD is-defined-SECRET_KEY container/build-builder
	@docker run --network sumario --rm -it                                  \
	    --name sumario.internal                                             \
	    -e GITLAB_USERNAME=$$GITLAB_USERNAME                                \
	    -e GITLAB_PASSWORD=$$GITLAB_PASSWORD                                \
	    -e POSTGRES_HOSTNAME=$$POSTGRES_HOSTNAME                            \
	    -e POSTGRES_TCP_PORT=$$POSTGRES_TCP_PORT                            \
	    -e POSTGRES_USERNAME=$$POSTGRES_USERNAME                            \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e SECRET_KEY=$$SECRET_KEY                                          \
	    -e SENTRY_DSN=$$SENTRY_DSN                                          \
	    -e SUMARIO_ENVIRONMENT=development                                  \
	    -e POSTMARK_TOKEN=$$POSTMARK_TOKEN                                  \
	    -e STRIPE_PUBKEY=$$STRIPE_PUBKEY                                    \
	    -e STRIPE_SECRET=$$STRIPE_SECRET                                    \
	    -e VERSION=$(VERSION)                                               \
	    -v sumario-backend-deps:/root/.local                                \
	    -v $(HERE)/sumario:/mnt/workdir                                     \
            $(BUILDER_IMAGE)                                                    \
	    make shell

.PHONY: sumario/exec-%
sumario/exec-%: has-command-docker
	@docker exec -it sumario.internal make $*

.PHONY: postgres/run
postgres/run: is-defined-POSTGRES_HOSTNAME is-defined-POSTGRES_TCP_PORT is-defined-POSTGRES_USERNAME is-defined-POSTGRES_PASSWORD container/create-network-sumario
	@docker run --network sumario --rm -it                                  \
	    --name $$POSTGRES_HOSTNAME                                          \
	    -e POSTGRES_PASSWORD=$$POSTGRES_PASSWORD                            \
	    -e POSTGRES_USER=$$POSTGRES_USERNAME                                \
	    -p $$POSTGRES_TCP_PORT:$$POSTGRES_TCP_PORT                          \
	    -v sumario-postgres-data:/var/lib/postgresql/data                   \
	    docker.io/library/postgres:15                                       \
	    -p $$POSTGRES_TCP_PORT

.PHONY: traefik/run
traefik/run: container/create-network-sumario
	@docker run --network sumario --rm                                      \
	    --name traefik.internal                                             \
	    --privileged                                                        \
	    -p 8080:8080                                                        \
	    -p 8443:8443                                                        \
	    -p 8675:8675                                                        \
	    -v $(HERE)/traefik:/mnt/workdir                                     \
	    -v /var/run/docker.sock:/var/run/docker.sock:ro                     \
	    -w /mnt/workdir                                                     \
	    docker.io/library/traefik:v2.10.4

FLY := $(HERE)/.bin/fly

.PHONY: fly/create-postgres
fly/create-postgres: is-defined-FLY_ORGANIZATION is-defined-POSTGRES_PASSWORD is-defined-SLUG
	@APPS="$$($(FLY) apps list)";                                           \
	if ! echo $$APPS | grep -cq sumario-postgres-$$SLUG; then               \
	    $(FLY) postgres create                                              \
	      -n sumario-postgres-$$SLUG                                        \
	      -o $$FLY_ORGANIZATION                                             \
	      -p $$POSTGRES_PASSWORD                                            \
	      -r scl;                                                           \
	fi                                                                      \

.PHONY: fly/set-slug
fly/set-slug: is-defined-SLUG has-command-sed
	@sed -i "s/@SLUG@/$$SLUG/g" *.toml

.PHONY: fly/create-infra
fly/create-infra: is-defined-FLY_ORGANIZATION is-defined-SLUG fly/create-postgres fly/set-slug
	@APPS="$$($(FLY) apps list)";                                           \
	for APP in backend; do                                                  \
	    if ! echo $$APPS | grep -cq sumario-$$APP-$$SLUG; then              \
	        $(FLY) apps create sumario-$$APP-$$SLUG -o $$FLY_ORGANIZATION;  \
	    fi;                                                                 \
	done

.PHONY: fly/destroy-infra
fly/destroy-infra: is-defined-SLUG
	@APPS="$$($(FLY) apps list)";                                           \
	for APP in postgres backend; do                                         \
	    if echo $$APPS | grep -cq sumario-$$APP-$$SLUG; then                \
	        $(FLY) apps destroy sumario-$$APP-$$SLUG -y;                    \
	    fi;                                                                 \
	done

.PHONY: fly/set-secrets
fly/set-secrets: export SECRETS=POSTGRES_HOSTNAME POSTGRES_TCP_PORT POSTGRES_USERNAME POSTGRES_PASSWORD POSTMARK_TOKEN SECRET_KEY SENTRY_DSN STRIPE_PUBKEY STRIPE_SECRET SUMARIO_ENVIRONMENT VERSION
fly/set-secrets: is-defined-POSTGRES_HOSTNAME is-defined-POSTGRES_TCP_PORT is-defined-POSTGRES_USERNAME is-defined-POSTGRES_PASSWORD is-defined-POSTMARK_TOKEN is-defined-SECRET_KEY is-defined-SENTRY_DSN is-defined-SLUG is-defined-STRIPE_PUBKEY is-defined-STRIPE_SECRET is-defined-SUMARIO_ENVIRONMENT is-defined-VERSION
	@for APP in backend; do                                                 \
	    echo "### Set secrets for $$APP-$$SLUG";                            \
	    SECRETS_LIST="$$($(FLY) secrets list -a sumario-$$APP-$$SLUG)";     \
	    for SECRET in $$SECRETS; do                                         \
	        $(FLY) secrets set -a sumario-$$APP-$$SLUG                      \
	          $$SECRET=$$(printenv $$SECRET) > /dev/null;                   \
	        echo "Set $$SECRET";                                            \
	    done;                                                               \
	done

.PHONY: fly/list-secrets
fly/list-secrets: is-defined-SLUG
	@for APP in postgres backend; do                                        \
	    echo "### Secrets set for $$APP-$$SLUG";                            \
	    $(FLY) secrets list -a sumario-$$APP-$$SLUG;                        \
	done

.PHONY: fly/deploy
fly/deploy: is-defined-SLUG fly/create-infra container/pull-release
	@for APP in backend; do                                                 \
	    echo "### Deploy $$APP-$$SLUG";                                     \
	    $(FLY) deploy -c sumario-$$APP.toml --vm-memory 2048                \
	      --local-only                                                      \
	      -i $(RELEASE_IMAGE);                                              \
	done

.PHONY: fly/status
fly/status: is-defined-SLUG
	@for APP in postgres backend; do                                        \
	    echo "### Status of $$APP-$$SLUG";                                  \
	    $(FLY) status -a sumario-$$APP-$$SLUG;                              \
	done

.PHONY: fly/forward-postgres
fly/forward-postgres: export DOCKER_EXTRA_RUN_ARGS=-p 5432:5432
fly/forward-postgres: is-defined-SLUG
	@$(FLY) proxy 5432:5432 -b 0.0.0.0 -a sumario-postgres-$$SLUG

.PHONY: fly/forward-backend
fly/forward-backend: export DOCKER_EXTRA_RUN_ARGS=-p 3000:3000
fly/forward-backend: is-defined-SLUG
	@$(FLY) proxy 3000:3000 -b 0.0.0.0 -a sumario-backend-$$SLUG
