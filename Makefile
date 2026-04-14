SHELL := /bin/bash

DOCKER ?= docker
COMPOSE := $(DOCKER) compose

DC_PROD := $(COMPOSE) -f docker-compose.yaml
DC_DEV  := $(COMPOSE) -f docker-compose.yaml -f docker-compose.override.yaml

ALEMBIC_SERVICE := migrations

MSG ?= 

.PHONY:	prod-up prod-build prod-stop prod-down prod-clean prod-logs \
	dev-up dev-build dev-stop dev-down dev-clean dev-logs \
	alembic-rev alembic-up alembic-down alembic-current alembic-history


prod-up:
	$(DC_PROD) up -d --remove-orphans

prod-build:
	$(DC_PROD) build

prod-stop:
	$(DC_PROD) stop

prod-down:
	$(DC_PROD) down --remove-orphans

prod-clean:
	$(DC_PROD) down -v --remove-orphans

prod-logs:
	$(DC_PROD) logs -f --tail=200



dev-up:
	$(DC_DEV) up -d --remove-orphans

dev-build:
	$(DC_DEV) build

dev-stop:
	$(DC_DEV) stop

dev-down:
	$(DC_DEV) down --remove-orphans

dev-clean:
	$(DC_DEV) down -v --remove-orphans

dev-logs:
	$(DC_DEV) logs -f --tail=200



alembic-rev:
	$(DC_DEV) run --rm $(ALEMBIC_SERVICE) alembic revision --autogenerate -m "$(MSG)"

alembic-up:
	$(DC_DEV) run --rm $(ALEMBIC_SERVICE) alembic upgrade head

alembic-down:
	$(DC_DEV) run --rm $(ALEMBIC_SERVICE) alembic downgrade -1

alembic-current:
	$(DC_DEV) run --rm $(ALEMBIC_SERVICE) alembic current

alembic-history:
	$(DC_DEV) run --rm $(ALEMBIC_SERVICE) alembic history