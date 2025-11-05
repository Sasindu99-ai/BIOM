MANAGER = python main.py
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
