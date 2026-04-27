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
	$(DC_PROD) --profile celery build

prod-stop:
	$(DC_PROD) --profile celery stop

prod-down:
	$(DC_PROD) --profile celery down --remove-orphans

prod-clean:
	$(DC_PROD) --profile celery down -v --remove-orphans

prod-logs:
	$(DC_PROD) --profile celery logs -f --tail=200

prod-worker:
	$(DC_PROD) --profile celery up -d

dev-up:
	$(DC_DEV) up -d --remove-orphans

dev-build:
	$(DC_DEV) --profile celery build

dev-stop:
	$(DC_DEV) --profile celery stop

dev-down:
	$(DC_DEV) --profile celery down --remove-orphans

dev-clean:
	$(DC_DEV) --profile celery down -v --remove-orphans

dev-logs:
	$(DC_DEV) --profile celery logs -f --tail=200

dev-worker:
	$(DC_DEV) --profile celery up -d


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

	

test-dispatch:
	$(DC_DEV) run --rm celery celery -A worker.celery_app call worker.tasks.scheduler_task.dispatch_due_crawls

test-link:
	$(DC_DEV) run --rm celery celery -A worker.celery_app call worker.tasks.get_source_link_task.get_source_links

prod-dispatch:
	$(DC_PROD) run --rm celery celery -A worker.celery_app call worker.tasks.scheduler_task.dispatch_due_crawls

prod-link:
	$(DC_PROD) run --rm celery celery -A worker.celery_app call worker.tasks.get_source_link_task.get_source_links

set-ready:
	docker exec -it ai-social-support-assistant-redis-1 redis-cli -n 1 SET "system:init_sources_status" "ready"