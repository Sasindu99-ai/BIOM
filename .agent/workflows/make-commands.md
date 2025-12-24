---
description: Makefile commands reference for development, building, database, and deployment operations
---

# Make Commands Reference

Quick reference for all available `make` commands in the project.

---

## Development Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make dev` | Run Vite dev server for hot-reload | **Terminal 1**: Always run during development |
| `make run` | Run Django development server | **Terminal 2**: Always run during development |
| `make build` | Build production assets with Vite | Before deployment |

> [!IMPORTANT]
> **Development Setup**: You need **TWO terminals** running simultaneously:
> 1. `make dev` - Vite server (handles Tailwind CSS, JS bundling)
> 2. `make run` - Django server (handles Python backend)

---

## Database Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make migrate` | Create and apply migrations | After model changes |
| `make make-migrations` | Create migration files only | Preview migrations before applying |
| `make execute-migrate` | Apply existing migrations | Apply pre-created migrations |
| `make superuser` | Create admin superuser | First-time setup |
| `make shell` | Open Django Python shell | Debug, test queries |
| `make db` | Open database shell | Direct DB access |

---

## Code Quality Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make lint` | Check code style with Ruff | Before committing |
| `make fix` | Auto-fix code style issues | Clean up code |

---

## Dependency Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make sync` | Sync Python dependencies with uv | After pulling changes |
| `make update` | sync + migrate combined | Quick project update |

---

## Command Details

### Development Workflow

```bash
# Terminal 1 - Start Vite (CSS/JS hot-reload)
make dev

# Terminal 2 - Start Django server
make run

# Visit: http://localhost:8000/
```

### Database Migration Workflow

```bash
# After modifying models:
make migrate

# Or step-by-step:
make make-migrations  # Creates migration files
make execute-migrate  # Applies migrations
```

### First-Time Setup

```bash
# 1. Install dependencies
make sync

# 2. Run migrations
make migrate

# 3. Create admin user
make superuser

# 4. Start development servers
make dev  # Terminal 1
make run  # Terminal 2
```

---

## Makefile Variables

```makefile
MANAGER = python main.py  # Django management script
PORT = 8000               # Default server port
```

---

## Underlying Commands

| Make Command | Actual Command |
|--------------|----------------|
| `make sync` | `uv sync` |
| `make lint` | `ruff check` |
| `make fix` | `ruff check --fix` |
| `make dev` | `npm run dev` |
| `make build` | `npm run build` |
| `make run` | `uv run python main.py runserver` |
| `make superuser` | `uv run python main.py createsuperuser` |