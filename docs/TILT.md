# Net-Con Development with Tilt and Kind

This project is configured for local Kubernetes development using Tilt and Kind.

## Prerequisites

- Docker
- kubectl
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [Tilt](https://docs.tilt.dev/install.html)
- [Task](https://taskfile.dev/installation/)
- envsubst (usually part of gettext package)

## Quick Start

1. Set up the local development environment:
   ```bash
   task local-setup
   ```

2. Start Tilt for live development:
   ```bash
   task tilt
   ```

   Or with custom configuration:
   ```bash
   tilt up -- --registry=myregistry.io/ --namespace=testing
   ```

3. Access the Tilt UI:
   - Open <http://localhost:10350> in your browser

## Available Commands

### Main Tasks

- `task` - Show all available tasks
- `task build` - Build the Docker image
- `task deploy` - Deploy as a one-time job pod (default)
- `task deploy -- pod` - Deploy as a one-time job pod
- `task deploy -- persistent` - Deploy as a persistent deployment
- `task local-setup` - Complete local development setup
- `task clean` - Clean up all resources

### Tilt Operations

- `task tilt:up` - Start Tilt for development
- `task tilt:up -- --host 0.0.0.0` - Start Tilt with custom args
- `task tilt:down` - Stop Tilt
- `task tilt:down -- --delete-namespaces` - Stop Tilt and clean namespaces

### Kind Cluster Management

- `task kind:create` - Create a local Kind cluster
- `task kind:delete` - Delete the Kind cluster
- `task kind:load` - Load the Docker image into Kind

### Kubernetes Operations

The kubernetes taskfile can be accessed via `k:`, `kubernetes:`, or `kubectl:` prefixes:

- `task k:get -- pods` - Get pods
- `task k:logs` - View logs with default settings
- `task k:logs -- <pod-name>` - View logs for specific pod
- `task k:logs -- -l app=net-con --since=1h` - View logs with custom filters
- `task k:exec -- <pod-name>` - Shell into a pod
- `task k:exec -- <pod-name> bash` - Run specific command in pod
- `task k:describe -- pod/<pod-name>` - Describe a resource
- `task k:port-forward -- <pod-name> 8080:80` - Port forward to a pod
- `task k:scale -- <deployment> 3` - Scale a deployment
- `task k:rollout -- status deployment/net-con` - Check rollout status
- `task k:top -- pods` - Show pod resource usage
- `task k:events` - Show events
- `task k:ns -- testing` - Switch to namespace
- `task k:ns` - Show current namespace
- `task k:ctx -- get-contexts` - List contexts
- `task k:debug -- <pod-name>` - Debug a pod with busybox

For raw kubectl access:

- `task k: -- <any kubectl command>` - Direct kubectl wrapper

### Deployment Operations

- `task deploy-pod` - Deploy as one-time pod
- `task deploy-persistent` - Deploy as persistent deployment
- `task deploy-status` - Show all resources
- `task deploy-status -- pods` - Show only pods
- `task deploy-status -- events` - Show events
- `task deploy-logs` - View deployment logs
- `task deploy-clean` - Clean up deployment resources

### Docker Operations

- `task docker:build` - Build the Docker image
- `task docker:run` - Run container locally
- `task docker:run -- -it --rm` - Run with custom docker args
- `task docker:exec` - Shell into running container
- `task docker:exec -- bash` - Run bash in container
- `task docker:buildx` - Build with buildx (default target)
- `task docker:buildx -- arm64` - Build for specific platform
- `task docker:push` - Push image to registry
- `task docker:up` - Start with docker-compose
- `task docker:down` - Stop docker-compose
- `task docker:logs` - View docker logs
- `task docker:prune` - Clean up Docker resources

### Development Workflow

1. **Initial Setup**: Run `task local-setup` once to create the Kind cluster and build the image
2. **Development**: Run `task tilt` to start live development with hot reload
3. **Testing**: Make changes to `main.py` - Tilt will automatically rebuild and redeploy
4. **Logs**: View logs in the Tilt UI or run the manual test trigger
5. **Cleanup**: Run `task tilt-down` when done

## Template Variables

The deployment template (`deployment.tpl.yml`) supports the following variables:

- `SERVICE` - Service name (default: "net-con")
- `VERSION` - Image version (default: "latest")
- `REGISTRY` - Container registry URL (default: "ghcr.io/")
- `NAMESPACE` - Kubernetes namespace (default: "default")
- `REPLICAS` - Number of replicas (default: 1)
- `CPU_LIMIT` - CPU limit (default: "100m")
- `MEMORY_LIMIT` - Memory limit (default: "128Mi")
- `CPU_REQUEST` - CPU request (default: "50m")
- `MEMORY_REQUEST` - Memory request (default: "64Mi")

Example with custom values:
```bash
task deploy-persistent NAMESPACE=testing REPLICAS=2 CPU_LIMIT=200m
```

## Tilt Features

- **Hot Reload**: Changes to `main.py` are automatically synced into the running container
- **Dependency Updates**: Changes to `pyproject.toml` or `uv.lock` trigger a rebuild
- **Manual Triggers**: 
  - `run-tests`: View latest test output
  - `cleanup-pods`: Remove completed test pods
- **Port Forwarding**: Automatically configured if your app exposes ports

## Troubleshooting

1. **Kind cluster not starting**: Ensure Docker is running and has enough resources
2. **Tilt not detecting changes**: Check `.tiltignore` file and ensure files aren't excluded
3. **Image not found**: Run `task kind-load` to load the image into Kind
4. **Permission errors**: Ensure your user has Docker and kubectl permissions

## CLI_ARGS Pattern

This project uses Task's `CLI_ARGS` feature extensively for flexible command execution. Arguments passed after `--` are captured and used by tasks:

```bash
# General pattern
task <task-name> -- <arguments>

# Examples
task deploy -- persistent           # Deploy as persistent deployment
task k -- get pods -o wide         # Run kubectl with custom args
task docker:buildx -- arm64         # Build for specific platform
task logs -- --since=1h            # View logs from last hour
```

Benefits:

- Single task handles multiple scenarios
- Reduces task duplication
- More intuitive command-line interface
- Better parameter passing to underlying tools

## Architecture

### Files Structure

- **Tiltfile**: Orchestrates the development environment
- **deployment.tpl.yml**: Template for Kubernetes manifests
- **Taskfile.yml**: Main task runner configuration with convenience aliases

### Taskfiles Organization

The project uses modular taskfiles for better organization:

- **Taskfile.yml**: Main orchestration with deployment tasks, convenience aliases
  - Contains all deployment logic (deploy-pod, deploy-persistent, deploy-status, etc.)
  - Provides convenience shortcuts (`up`, `down`, `logs`, `exec`, `status`)
- **taskfiles/docker.yml**: Docker operations (build, run, exec, compose, buildx)
- **taskfiles/k8s.yml**: Kubectl wrapper and common K8s operations
  - Accessible via `k:`, `kubernetes:`, or `kubectl:` prefixes
  - Provides shortcuts for common kubectl commands
  - All tasks support CLI_ARGS for flexible parameter passing
- **taskfiles/kind.yml**: Kind cluster management (create, delete, load images)
- **taskfiles/tilt.yml**: Tilt operations (up, down with CLI_ARGS support)
- **taskfiles/uv.yml**: Python/UV dependency management

### Task Naming Convention

- **Namespaced tasks**: `<namespace>:<task>` (e.g., `docker:build`, `k:logs`)
- **Aliases**: Multiple ways to access the same functionality
  - `k:`, `kubernetes:`, `kubectl:` all point to kubernetes.yml
  - Main taskfile provides shortcuts like `up`, `down`, `logs`, `exec`
- **CLI_ARGS pattern**: Most tasks accept `-- <arguments>` for flexibility
