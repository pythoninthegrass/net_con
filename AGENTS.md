# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

net_con is a Python 3.13 network connectivity testing tool that verifies TCP connections, HTTP/HTTPS requests, and DNS resolution. It's designed to run on both bare metal and containerized workloads.

## Architecture

- **Single-file application**: `main.py` contains all testing functions
- **Standalone script**: Uses PEP 723 inline dependencies for direct execution
- **Minimal dependencies**: Only uses `requests` library plus Python standard library
- **Containerized**: Docker image based on Python 3.13-slim with multi-platform builds
- **Kubernetes-ready**: Includes deployment templates and Tilt configuration
- **Testing**: pytest test suite in `tests/` directory

## Development Commands

### Environment Setup

```bash
# Check prerequisites (Docker, kubectl)
task check-prereqs

# Complete local development setup
task local-setup

# Create and sync virtual environment
task uv:venv
task uv:sync
```

### Running the Application

```bash
# Run as standalone script (PEP 723 - auto-installs dependencies)
./main.py

# Run locally with uv
uv run python main.py

# Build and run in Docker
task build
task docker:run

# Development with Tilt
task up    # Start Tilt
task down  # Stop Tilt

# View logs and status
task logs
task status
task exec  # Exec into container
```

### Testing

```bash
# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=main tests/
```

### Code Quality (Required Before Commits)

```bash
# Format code
ruff format .

# Check formatting and linting
ruff format --check --diff .

# Run all pre-commit hooks
pre-commit run --all-files
```

## Code Style

- **Line length**: 130 characters
- **Indentation**: 4 spaces
- **Python version**: 3.13+ required (strict, <3.14)
- **Package management**: Use `uv` exclusively
- **Linting**: 
  - `ruff` with pycodestyle, Pyflakes, pyupgrade, flake8-bugbear, flake8-simplify, isort
  - `markdownlint -f -c .markdownlint.jsonc *.md`

## Task Runner

Uses Task (taskfile.dev) with organized taskfiles in `taskfiles/` directory:

- `bootstrap.yml`: Logging and container execution operations
- `uv.yml`: Python/uv operations
- `docker.yml`: Container operations with multi-platform builds
- `kind.yml`: Local Kubernetes cluster management
- `tilt.yml`: Development workflow with live reloading
- `k8s.yml`: Kubernetes operations (aliased as kubectl, kubernetes, k)

## Project Structure

```
├── main.py              # Main application (PEP 723 script)
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── tests/              # pytest test suite
├── taskfiles/          # Task runner configurations
├── docs/               # Documentation
├── Dockerfile          # Multi-stage container build
├── docker-bake.hcl     # Docker buildx configuration
├── Tiltfile            # Tilt development configuration
├── deployment.tpl.yml  # Kubernetes deployment template
└── TODO.md             # Project tasks and improvements
```

## Development Workflow

1. Make code changes
2. Run `ruff format .` for formatting
3. Test locally with `./main.py` or `uv run python main.py`
4. Run tests with `pytest tests/`
5. Run `pre-commit run --all-files` before committing
6. For container changes, test with `task build && task docker:run`

## Runtime Management

- **Python version**: Managed by mise (`.tool-versions`)
- **Virtual environment**: Managed by uv in `.venv/`
- **Dependencies**: Locked in `uv.lock` with exclude-newer constraint
- **Container user**: Runs as non-root `appuser`
- **Multi-platform builds**: Supports linux/amd64 and linux/arm64
