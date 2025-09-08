# -*- mode: Python -*-

# Load extensions
load('ext://restart_process', 'docker_build_with_restart')

# Configuration
config.define_string("registry", args=False, usage="Container registry URL")
config.define_string("namespace", args=False, usage="Kubernetes namespace to deploy to")
cfg = config.parse()

# Set default values from environment variables with fallbacks
default_registry = os.getenv("REGISTRY", "ghcr.io")

# Check if ctlptl kind cluster exists and use local registry
if str(local('ctlptl get cluster kind-kind >/dev/null 2>&1; echo $?', quiet=True)).strip() == "0":
    default_registry = "localhost:5005"

registry = cfg.get("registry") or default_registry
namespace = cfg.get("namespace") or os.getenv("NAMESPACE", "default")
service_name = os.getenv("SERVICE", "net-con")
version = os.getenv("VERSION", "latest")

# Ensure we're using kind
allow_k8s_contexts('kind-kind')

# Create namespace if it doesn't exist
k8s_yaml(blob("""
apiVersion: v1
kind: Namespace
metadata:
  name: {}
""".format(namespace)))

# Build the Docker image with hot reload
# Use the image name from the deployment template for consistency
image_name = '{}/{}:{}'.format(os.getenv("REGISTRY", "ghcr.io"), service_name, version)
docker_build_with_restart(
    image_name,
    '.',
    dockerfile='Dockerfile',
    entrypoint=['sh', '-c', 'export UV_CACHE_DIR=/tmp/.cache/uv && export UV_NO_SYNC=1 && uv run python main.py'],
    only=[
        './main.py',
        './pyproject.toml',
        './uv.lock'
    ],
    live_update=[
        sync('./main.py', '/app/main.py'),
        run('cd /app && export UV_CACHE_DIR=/tmp/.cache/uv && export UV_NO_SYNC=1 && uv sync --frozen', trigger=['./pyproject.toml', './uv.lock']),
        run('touch /tmp/.restart-proc', trigger=['./main.py']),
    ],
)

# Generate deployment YAML from template using Task
deployment_yaml = local('task bootstrap:template -- deployment', quiet=True)

# Apply the deployment YAML
k8s_yaml(deployment_yaml)

# Configure the Kubernetes resource
k8s_resource(
    service_name,
    port_forwards="8080:8080",  # Forward port if the app exposes one
    labels=["net-con"],
)

# Add a local resource to run connectivity tests
local_resource(
    'run-tests',
    cmd='kubectl logs -n {} -l app={} --tail=100'.format(namespace, service_name),
    deps=['./main.py'],
    labels=["tests"],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Add a resource to clean up completed pods
local_resource(
    'cleanup-pods',
    cmd='kubectl delete pods -n {} -l app={} --field-selector=status.phase==Succeeded'.format(namespace, service_name),
    labels=["maintenance"],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)
