# -*- mode: Python -*-

# Load extensions
load('ext://restart_process', 'docker_build_with_restart')

# Configuration
config.define_string("registry", args=False, usage="Container registry URL")
config.define_string("namespace", args=False, usage="Kubernetes namespace to deploy to")
config.parse()

# Set default values
registry = cfg.get("registry", "ghcr.io/")
namespace = cfg.get("namespace", "default")
service_name = "net-con"
version = "latest"

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
docker_build_with_restart(
    '{}{}'.format(registry, service_name),
    '.',
    dockerfile='Dockerfile',
    entrypoint=['uv', 'run', 'python', 'main.py'],
    only=[
        './main.py',
        './pyproject.toml',
        './uv.lock'
    ],
    live_update=[
        sync('./main.py', '/app/main.py'),
        run('cd /app && uv sync --frozen', trigger=['./pyproject.toml', './uv.lock']),
    ],
)

# Apply the deployment template
k8s_yaml('deployment.tpl.yml')

# Configure the Kubernetes resource
k8s_resource(
    service_name,
    port_forwards="8080:8080",  # Forward port if the app exposes one
    resource_deps=['namespace'],
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

# Print startup information
print("""
╔══════════════════════════════════════════════════════════════╗
║                   Net-Con Development Setup                  ║
╠══════════════════════════════════════════════════════════════╣
║ Service: {}                                                  ║
║ Namespace: {}                                                ║
║ Registry: {}                                                 ║
╠══════════════════════════════════════════════════════════════╣
║ Available Commands:                                          ║
║   • Press 'r' to rebuild                                     ║
║   • Press 'l' to view logs                                   ║
║   • Run 'tilt trigger run-tests' to execute tests            ║
║   • Run 'tilt trigger cleanup-pods' to clean up old pods     ║
╚══════════════════════════════════════════════════════════════╝
""".format(service_name.ljust(48), namespace.ljust(47), registry.ljust(43)))
