# GitHub Actions Kubernetes Deployment Portfolio Project

This repository demonstrates a realistic DevOps CI/CD workflow for a containerized application deployed to Kubernetes with Minikube.

It includes a Python Flask service, Docker image build and security scanning, branch-based environment selection, Docker Hub publishing, Kustomize overlays for test/dev/prod, direct Minikube deployment support for self-hosted GitHub Actions runners, and clear deployment summaries.

## Architecture

```text
Developer push
     |
     v
GitHub Actions
     |
     +--> Detect branch environment
     |       test      -> test
     |       feature/* -> test
     |       develop   -> dev
     |       main      -> prod
     |       hotfix/*  -> prod
     |
     +--> Python syntax, lint, and unit tests
     |
     +--> Docker build
     |
     +--> Trivy image scan
     |       HIGH/CRITICAL findings fail the pipeline
     |
     +--> Push image to Docker Hub
     |       docker.io/<dockerhub-user>/k8s-deployment:<env>-<sha>
     |
     +--> Deploy to Minikube when a Kubernetes cluster is reachable
             GitHub-hosted runner: normally skipped
             Self-hosted runner with Minikube: applies Kustomize overlay
```

## Technologies Used

- Python 3.12
- Flask
- Pytest
- Ruff
- Docker
- GitHub Actions
- Docker Hub
- Trivy
- Kubernetes
- Kustomize
- Minikube

## Repository Structure

```text
.
├── .github/
│   ├── actions/
│   │   ├── app-checks/
│   │   ├── check-kubernetes-access/
│   │   ├── deploy-kustomize/
│   │   ├── deploy-summary/
│   │   ├── detect-environment/
│   │   ├── docker-build/
│   │   ├── docker-image-metadata/
│   │   ├── export-docker-image/
│   │   ├── load-docker-image/
│   │   ├── push-docker-image/
│   │   └── verify-deployment/
│   └── workflows/
│       └── ci-cd.yml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   └── tests/
├── k8s/
│   ├── base/
│   └── overlays/
│       ├── dev/
│       ├── prod/
│       └── test/
├── screenshots/
│   └── README.md
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Application Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Returns app name, environment, version, and hostname. |
| GET | `/health` | Returns health status for probes and load balancers. |

## Branch-to-Environment Mapping

| Branch pattern | Environment | Namespace | Ingress host |
| --- | --- | --- | --- |
| `test` | `test` | `devops-demo-test` | `test.devops-demo.local` |
| `feature/*` | `test` | `devops-demo-test` | `test.devops-demo.local` |
| `develop` | `dev` | `devops-demo-dev` | `dev.devops-demo.local` |
| `main` | `prod` | `devops-demo-prod` | `prod.devops-demo.local` |
| `hotfix/*` | `prod` | `devops-demo-prod` | `prod.devops-demo.local` |

Any other branch stops the workflow with a clear error. This makes environment promotion explicit and prevents accidental deployments from unexpected branches.

## Required Secrets and Variables

Docker Hub is the only image publishing target used by this project.

Required GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `REGISTRY_USERNAME` | Docker Hub username or organization. |
| `REGISTRY_TOKEN` | Docker Hub access token used by GitHub Actions to push images. |

Optional GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `REGISTRY_PASSWORD` | Fallback Docker Hub password if `REGISTRY_TOKEN` is not available. A Docker Hub access token is preferred. |

Optional repository variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MINIKUBE_RUNNER` | `ubuntu-latest` | Set to a self-hosted runner label such as `self-hosted` or `minikube` to deploy directly to local Minikube. |

## Image Tagging

The workflow creates environment-aware image tags:

```text
docker.io/<REGISTRY_USERNAME>/k8s-deployment:test-<short_sha>
docker.io/<REGISTRY_USERNAME>/k8s-deployment:dev-<short_sha>
docker.io/<REGISTRY_USERNAME>/k8s-deployment:prod-<short_sha>
docker.io/<REGISTRY_USERNAME>/k8s-deployment:latest
```

The `latest` tag is only pushed from the `main` branch.

## Run the App Locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements-dev.txt
APP_ENV=local APP_VERSION=0.1.0 python -m app.main
```

Verify it:

```bash
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
```

Run checks locally:

```bash
python -m py_compile app/main.py app/__init__.py app/tests/test_main.py
ruff check app
pytest -q app/tests
```

## Build and Run Docker Locally

```bash
docker build -t devops-k8s-demo:local .
docker run --rm -p 8080:8080 \
  -e APP_ENV=local \
  -e APP_VERSION=0.1.0 \
  devops-k8s-demo:local
```

Verify the container:

```bash
curl http://127.0.0.1:8080/health
```

## Kubernetes Manifests

The Kubernetes manifests use Kustomize:

- `k8s/base` contains shared Kubernetes resources.
- `k8s/overlays/test` customizes the test namespace, replicas, resources, config, HPA, and ingress hostname.
- `k8s/overlays/dev` customizes the dev namespace, replicas, resources, config, HPA, and ingress hostname.
- `k8s/overlays/prod` customizes the prod namespace, replicas, resources, config, HPA, and ingress hostname.

Included Kubernetes resources:

- Namespace
- Deployment
- ClusterIP Service
- Ingress
- ConfigMap
- HorizontalPodAutoscaler

The Deployment includes:

- Non-root container execution
- Dropped Linux capabilities
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- Resource requests and limits
- Readiness and liveness probes
- Rolling update strategy
- ConfigMap-driven environment variables

## Start Minikube

```bash
minikube start
minikube addons enable ingress
minikube addons enable metrics-server
```

The ingress addon is required for Ingress resources. The metrics-server addon is required for the HPA to receive CPU metrics.

## Manual Minikube Deployment

Approach A is the normal flow when using GitHub-hosted runners:

1. GitHub Actions builds the image, scans it in a separate job, and pushes it only after the scan passes.
2. You deploy manually to local Minikube because GitHub-hosted runners cannot access your local cluster.

For a fully local test without pulling from Docker Hub, build the image inside Minikube's Docker daemon:

```bash
eval "$(minikube docker-env)"
docker build -t devops-k8s-demo:local .
kubectl apply -k k8s/overlays/dev
kubectl rollout status deployment/devops-k8s-demo -n devops-demo-dev
```

To deploy an image pushed by GitHub Actions:

```bash
IMAGE=docker.io/<dockerhub-user>/k8s-deployment:dev-<short_sha>
kubectl apply -k k8s/overlays/dev
kubectl set image deployment/devops-k8s-demo web="$IMAGE" -n devops-demo-dev
kubectl rollout status deployment/devops-k8s-demo -n devops-demo-dev
```

If the Docker Hub repository is private, either make it public for the demo or create a Kubernetes image pull secret.

## Access the App in Minikube

Port-forwarding works without DNS changes:

```bash
kubectl port-forward svc/devops-k8s-demo 8080:80 -n devops-demo-dev
curl http://127.0.0.1:8080/
```

Ingress access requires the Minikube ingress addon and local hostnames:

```bash
minikube ip
```

Add entries like this to `/etc/hosts`, replacing the IP with your Minikube IP:

```text
192.168.49.2 test.devops-demo.local
192.168.49.2 dev.devops-demo.local
192.168.49.2 prod.devops-demo.local
```

Then verify:

```bash
curl http://dev.devops-demo.local/
```

## Verify Kubernetes Resources

```bash
kubectl get pods -n devops-demo-dev
kubectl get svc -n devops-demo-dev
kubectl get ingress -n devops-demo-dev
kubectl describe deployment devops-k8s-demo -n devops-demo-dev
kubectl logs -l app.kubernetes.io/name=devops-k8s-demo -n devops-demo-dev
```

## GitHub Actions Workflow

The workflow is defined in `.github/workflows/ci-cd.yml`.

Jobs:

1. `detect-environment`
   - Checks out the repository.
   - Uses a composite action to map the branch to `test`, `dev`, or `prod`.
   - Fails fast on unsupported branch names.

2. `app-checks`
   - Installs Python dependencies.
   - Runs `python -m py_compile`.
   - Runs Ruff linting.
   - Runs Pytest unit tests.
   - Runs before Docker image build.

3. `build-image`
   - Builds the Docker image.
   - Exports the built image as a short-lived workflow artifact so the next jobs can use the exact same image.

4. `scan-image`
   - Downloads and loads the Docker image built by `build-image`.
   - Scans the built image with Trivy.
   - Reports all vulnerability severities.
   - Fails on HIGH or CRITICAL vulnerabilities.

5. `push-image`
   - Downloads and loads the scanned Docker image.
   - Pushes the image only after the scan passes.

6. `deploy-minikube`
   - Checks for `kubectl` and a reachable Kubernetes cluster.
   - Skips direct deployment on GitHub-hosted runners without cluster access.
   - Applies the correct Kustomize overlay when Minikube is reachable.
   - Sets the Deployment image to the image built in the workflow.
   - Verifies rollout, pods, Service, and Ingress.
   - Exposes the final deployment status for the summary job.

7. `deployment-summary`
   - Runs after `deploy-minikube` with `if: always()`.
   - Writes a deployment summary even when deployment or rollout verification fails.

## Direct Deployment to Minikube

Approach B uses a self-hosted GitHub Actions runner on the same machine where Minikube is running.

High-level setup:

1. Install a self-hosted GitHub Actions runner on your machine.
2. Start Minikube on that machine.
3. Confirm the runner user can run `kubectl get nodes` using its local Kubernetes context.
4. Set repository variable `MINIKUBE_RUNNER` to the runner label, for example `self-hosted` or `minikube`.
5. Run the workflow from a supported branch.

The workflow still works without this setup. On GitHub-hosted runners it runs checks, builds, scans, and pushes the image, then skips direct deployment because local Minikube is not reachable.

## Trivy Vulnerability Scanning

The workflow scans the built Docker image with Trivy before pushing it.

Policy:

- LOW and MEDIUM vulnerabilities are reported but do not fail the pipeline.
- HIGH and CRITICAL vulnerabilities fail the pipeline with exit code `1`.
- The scan output is readable in the GitHub Actions logs.

This makes the security gate visible and easy to explain during a portfolio review.

## Security Practices Demonstrated

- No real secrets committed.
- GitHub Secrets used for Docker Hub credentials.
- Container runs as a non-root user.
- Pod and container security contexts restrict privileges.
- Resource requests and limits are defined.
- Readiness and liveness probes are configured.
- Branches map to isolated Kubernetes namespaces.
- Trivy blocks HIGH and CRITICAL image vulnerabilities.
- Deployment verification runs after applying manifests.

## Screenshots to Add

See `screenshots/README.md` for the screenshot checklist. Useful screenshots include:

- Successful GitHub Actions pipeline
- Trivy scan output
- Image published in Docker Hub
- `kubectl get pods`
- `kubectl get svc`
- `kubectl get ingress`
- Application opened in browser
- Deployment rollout status

## How This Project Can Be Described on a CV

- Built a GitHub Actions CI/CD pipeline for a containerized Flask application, including syntax checks, linting, unit tests, Docker image build, Trivy vulnerability scanning, image publishing, and Kubernetes deployment.
- Implemented Kubernetes manifests with Kustomize overlays for test, dev, and prod environments, including ConfigMaps, probes, resource limits, HPA, and Ingress for Minikube.
- Added branch-based environment selection, deployment verification, and automated GitHub Actions deployment summaries for clear release visibility.
