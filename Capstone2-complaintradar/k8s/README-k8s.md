# ComplaintRadar on Kubernetes (Kind / Minikube)

Use a **local** cluster. Do not apply these manifests to a shared production context.

```bash
# 1. Create Kind cluster
kind create cluster --name complaintradar-cluster

# 2. Point kubectl at Kind (if you also have remote contexts)
kind export kubeconfig --name complaintradar-cluster --kubeconfig ~/.kube/config
kubectl config use-context kind-complaintradar-cluster

# 3. Build and load the app image
docker build -t complaintradar-app:latest .
kind load docker-image complaintradar-app:latest --name complaintradar-cluster

# 4. Apply manifests
kubectl apply -f k8s/
kubectl get pods

# 5. Port-forward
kubectl port-forward svc/complaintradar-app 8501:8501
kubectl port-forward svc/complaintradar-grafana 3000:3000
```

- App: http://127.0.0.1:8501
- Grafana: http://127.0.0.1:3000 (`admin` / `admin`)

Cleanup:

```bash
kind delete cluster --name complaintradar-cluster
```
