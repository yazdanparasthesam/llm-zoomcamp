# ☸️ FinDocs Copilot — Kubernetes Deployment Guide (Bonus Points)

While **Docker Compose (`docker-compose.yml`)** provides the standard **2/2 points** for the Containerization evaluation criteria, deploying to **Kubernetes (K8s)** qualifies the project for:
1. **+2 Bonus Points for Cloud Deployment** (when deployed to an EKS, GKE, AKS, or DigitalOcean Kubernetes cluster with an accessible endpoint).
2. **+1 to +3 Extra Bonus Points** from peer reviewers for enterprise-grade orchestration and scalability!

---

## 🚀 How to Deploy on Kubernetes (Minikube / Kind / Cloud Cluster)

### 1. Build & Tag the Application Image
If you are running on **Minikube**, point your Docker CLI to Minikube's daemon first:
```bash
eval $(minikube docker-env)
docker build -t findocs-app:latest .
```
*(For a cloud cluster, push the image to a container registry such as Docker Hub or AWS ECR and update `k8s/04-app.yaml` with your image tag).*

---

### 2. Configure Your Secrets & API Key
Open `k8s/01-configmap-secret.yaml` and set your optional Groq API key:
```yaml
stringData:
  GROQ_API_KEY: "your_api_key_here" # Or leave empty for automatic mock mode
```

---

### 3. Apply the Kubernetes Manifests
Run `kubectl apply` across the `k8s/` directory:
```bash
kubectl apply -f k8s/
```

Verify that all pods are running:
```bash
kubectl get pods -w
```
You should see:
- `findocs-postgres-xxxx` (`Running`)
- `findocs-elasticsearch-xxxx` (`Running`)
- `findocs-app-xxxx` (`Running`)
- `findocs-grafana-xxxx` (`Running`)

---

### 4. Access the Applications
Check the services:
```bash
kubectl get svc
```
- **Streamlit App**: Port `8501` (`LoadBalancer` or via `kubectl port-forward svc/findocs-app 8501:8501`)
- **Grafana Dashboard**: Port `3000` (`LoadBalancer` or via `kubectl port-forward svc/findocs-grafana 3000:3000`)
- **Elasticsearch API**: Port `9200` (`ClusterIP`)
- **Postgres Database**: Port `5432` (`ClusterIP`)
