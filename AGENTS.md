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

# Development with Tilt (auto-creates kind cluster with ctlptl)
task up    # Start Tilt (creates cluster + registry automatically)
task down  # Stop Tilt

# View logs and status
task logs
task status
task exec  # Exec into container

# Clean up everything (Tilt + cluster)
task tilt:destroy
```

### Cluster Management

```bash
# Manual cluster operations (ctlptl-managed)
task kind:create        # Create kind-kind cluster with local registry
task kind:delete        # Delete cluster and registry
task kind:registry-url  # Get local registry URL (localhost:5005)

# Check cluster status
ctlptl get clusters
kubectl cluster-info --context kind-kind

# Registry operations
docker push localhost:5005/my-image  # Push images to local registry
```

**ctlptl Integration Benefits:**
- **Declarative cluster management**: Cluster configuration defined in YAML
- **Automatic registry setup**: Local registry at `localhost:5005` created automatically  
- **Fast image builds**: No network dependency, ~900ms image pulls vs several seconds
- **Tilt auto-detection**: Automatically uses local registry when available
- **Consistent naming**: Cluster named `kind-kind` following kind conventions

### Debugging Tiltfiles

```bash
# Stream logs directly to terminal (useful for debugging)
task up -- --stream=true

# Run in legacy terminal mode
task up -- --legacy=true

# Validate Tiltfile without running
tilt ci

# Check Tiltfile syntax
tilt dump cli-analytics

# Run with verbose output
tilt up --verbose

# Run with specific Tiltfile arguments
tilt up -- --arg=value

# Manual trigger for test execution
tilt trigger run-tests

# Clean up completed pods
tilt trigger cleanup-pods
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
- `kind.yml`: Local Kubernetes cluster management using ctlptl
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
6. For container changes, test with:
   - **Local containers**: `task build && task docker:run`
   - **Kubernetes**: `task up` (auto-creates cluster, builds image, deploys)
7. Clean up when done: `task tilt:clean` (removes cluster + registry)

## Runtime Management

- **Python version**: Managed by mise (`.tool-versions`)
- **Virtual environment**: Managed by uv in `.venv/`
- **Dependencies**: Locked in `uv.lock` with exclude-newer constraint
- **Container user**: Runs as non-root `appuser`
- **Multi-platform builds**: Supports linux/amd64 and linux/arm64

## Environment Configuration

The project uses environment variables for configuration, loaded from `.env` file by Task:

```bash
# Copy example configuration
cp .env.example .env

# Edit .env to set your values
SERVICE=net-con        # Service name
VERSION=latest         # Image version
REGISTRY=ghcr.io      # Container registry (no trailing slash)
NAMESPACE=default      # Kubernetes namespace
```

Both Task and Tilt read these environment variables:
- Task: Automatically loads `.env` file
- Tilt: Reads from environment (set by Task or system)
- **Local Registry**: When using ctlptl, Tilt automatically detects the local registry at `localhost:5005` and uses it instead of the configured `REGISTRY`
