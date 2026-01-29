MANAGER = python manage.py
PORT = 8000

# Sync dependencies
.PHONY: sync
sync:
	uv sync

# Check code style
.PHONY: lint
lint:
	ruff check

# Fix code style
.PHONY: fix
fix:
	ruff check --fix

# Run vite dev server
.PHONY: dev
dev:
	npm run dev

# Build the project
.PHONY: build
build:
	npm run build

# Run Django production server
.PHONY: run
run:
	uv run $(MANAGER) runserver

# Make migrations
.PHONY: make-migrations
make-migrations:
	uv run $(MANAGER) makemigrations authentication settings main

# Execute migrations
.PHONY: execute-migrate
execute-migrate:
	uv run $(MANAGER) migrate

# Make and execute migrations
.PHONY: migrate
migrate: make-migrations execute-migrate ;

# Create a superuser
.PHONY: superuser
superuser:
	uv run $(MANAGER) createsuperuser

# Django shell
.PHONY: shell
shell:
	uv run $(MANAGER) shell

# Django DB shell
.PHONY: db
db:
	uv run $(MANAGER) dbshell

# Update project dependencies
.PHONY: update
update: sync migrate ;

# Run Django-Q worker for background jobs
.PHONY: worker
worker:
	uv run $(MANAGER) qcluster

.PHONY: check
check:
	uv run $(MANAGER) check

.PHONY: up-deps
up-deps:
# 	test -f .env || cp .env.example .env
	docker-compose -f docker-compose.dev.yml up --force-recreate db

.PHONY: collectstatic
collectstatic:
	uv run $(MANAGER) collectstatic --no-input
