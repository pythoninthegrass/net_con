# -*- mode: Python -*-

load('ext://restart_process', 'docker_build_with_restart')

config.define_string("registry", args=False, usage="Container registry URL")
config.define_string("namespace", args=False, usage="Kubernetes namespace to deploy to")
cfg = config.parse()

default_registry = os.getenv("REGISTRY", "ghcr.io")

if str(local('ctlptl get cluster kind-kind >/dev/null 2>&1; echo $?', quiet=True)).strip() == "0":
    default_registry = "localhost:5005"

registry = cfg.get("registry") or default_registry
namespace = cfg.get("namespace") or os.getenv("NAMESPACE", "default")
service_name = os.getenv("SERVICE", "net-con")
version = os.getenv("VERSION", "latest")

allow_k8s_contexts('kind-kind')

k8s_yaml(blob("""
apiVersion: v1
kind: Namespace
metadata:
  name: {}
""".format(namespace)))

image_name = '{}/{}:{}'.format(os.getenv("REGISTRY", "ghcr.io"), service_name, version)

docker_build(
    image_name,
    '.',
    dockerfile='Dockerfile',
    only=[
        './main.py',
        './pyproject.toml',
        './uv.lock'
    ],
    live_update=[
        sync('./main.py', '/app/main.py'),
        run('cd /app && export UV_CACHE_DIR=/tmp/.cache/uv && export UV_NO_SYNC=1 && uv sync --frozen', trigger=['./pyproject.toml', './uv.lock']),
    ],
)

deployment_yaml = local('task bootstrap:template -- deployment', quiet=True)

k8s_yaml(deployment_yaml)

k8s_resource(
    service_name,
    port_forwards="8080:8080",
    labels=["net-con"],
)

local_resource(
    'run-tests',
    cmd='kubectl exec -n {} deployment/{} -- uv run python main.py'.format(namespace, service_name),
    deps=['./main.py'],
    labels=["tests"],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource(
    'view-logs',
    cmd='kubectl logs -n {} deployment/{} --tail=50'.format(namespace, service_name),
    labels=["tests"],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

local_resource(
    'cleanup-pods',
    cmd='kubectl delete pods -n {} -l app={} --field-selector=status.phase==Succeeded'.format(namespace, service_name),
    labels=["maintenance"],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)
