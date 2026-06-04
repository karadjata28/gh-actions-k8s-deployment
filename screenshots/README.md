# Screenshots Checklist

Add screenshots here after running the project locally and in GitHub Actions.

Recommended screenshots:

1. GitHub Actions successful pipeline showing all jobs.
2. GitHub Actions environment detection log.
3. Trivy scan output showing the HIGH/CRITICAL security gate.
4. Docker image published in Docker Hub.
5. `kubectl get pods -n devops-demo-dev`.
6. `kubectl get svc -n devops-demo-dev`.
7. `kubectl get ingress -n devops-demo-dev`.
8. `kubectl describe deployment devops-k8s-demo -n devops-demo-dev`.
9. `kubectl rollout status deployment/devops-k8s-demo -n devops-demo-dev`.
10. Application opened in a browser through port-forwarding or Ingress.

Suggested file names:

```text
github-actions-success.png
trivy-scan.png
dockerhub-image.png
kubectl-pods.png
kubectl-service.png
kubectl-ingress.png
deployment-describe.png
rollout-status.png
app-browser.png
```
