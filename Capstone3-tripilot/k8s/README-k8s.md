# Kubernetes deployment (local Kind)

Deploy TripPilot only to the dedicated **local** `kind-tripilot-cluster` context.
Do not apply these development manifests to a shared or production cluster.
Prerequisites: Docker, Kind, and kubectl, plus the service images from the
Docker Compose run. Keep `k8s/` and the dashboard JSON at the same repository revision.

The commands stop Compose without deleting its PostgreSQL data. Kubernetes
uses a separate, ephemeral PostgreSQL deployment; submit new interactions in
the Kubernetes-served app to populate its dashboard.

```bash
cd ~/Documents/tripilot                    # enter the project root with the current deployment files

# Check prerequisites before stopping the running Compose stack.
docker version                            # verify both Docker client and daemon are available
kind version                              # verify the local-cluster CLI is installed
kubectl version --client                  # verify the Kubernetes client is installed

docker compose stop                      # free host ports while retaining Compose containers and the PostgreSQL volume
kind create cluster --name tripilot-cluster  # create a dedicated local Kubernetes cluster
kubectl config use-context kind-tripilot-cluster  # select this local cluster rather than another environment
kubectl config current-context            # confirm kind-tripilot-cluster before applying any resources

docker build -t tripilot-app:latest .      # build the current app image from the project root
kind load docker-image tripilot-app:latest postgres:16 grafana/grafana:10.2.3 \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.1 --name tripilot-cluster  # load all four local images without cluster-side downloads
kubectl --context=kind-tripilot-cluster create configmap tripilot-grafana-dashboard \
  --from-file=tripilot_dashboard.json=grafana/dashboards/tripilot_dashboard.json \
  --dry-run=client -o yaml | kubectl --context=kind-tripilot-cluster apply -f -  # create or update the dashboard ConfigMap
kubectl --context=kind-tripilot-cluster apply -f k8s/  # apply configuration, secrets, services, and deployments

kubectl --context=kind-tripilot-cluster rollout status deployment/tripilot-postgres --timeout=300s  # wait for PostgreSQL readiness
kubectl --context=kind-tripilot-cluster rollout status deployment/tripilot-elasticsearch --timeout=300s  # wait for the ES deployment
kubectl --context=kind-tripilot-cluster rollout status deployment/tripilot-app --timeout=300s  # wait for the app health probe
kubectl --context=kind-tripilot-cluster rollout status deployment/tripilot-grafana --timeout=300s  # wait for the Grafana deployment
kubectl --context=kind-tripilot-cluster get pods,svc  # inspect all four workloads and their services

# Terminal 1: leave this app port-forward running.
kubectl --context=kind-tripilot-cluster port-forward svc/tripilot-app 8501:8501  # expose the app at http://localhost:8501
# Terminal 2: leave this Grafana port-forward running.
kubectl --context=kind-tripilot-cluster port-forward svc/tripilot-grafana 3000:3000  # expose Grafana at http://localhost:3000
# Terminal 3: check the forwarded endpoints.
curl -fsS http://localhost:8501/healthz && echo  # verify the Kubernetes-served app responds
curl -fsS http://localhost:3000/api/health | python3 -m json.tool  # verify the forwarded Grafana endpoint

# Open the app, submit requests and feedback, and confirm Monitoring reports postgres.
# Open http://localhost:3000/d/tripilot-monitoring (admin/admin) and inspect the six populated panels.
```

## Grafana provisioning

`05-grafana.yaml` projects the `tripilot-grafana-files` ConfigMap as:

- `/etc/grafana/provisioning/datasources/datasources.yaml`
- `/etc/grafana/provisioning/dashboards/dashboards.yaml`

The dashboard ConfigMap is mounted at `/var/lib/grafana/dashboards`.
Create it from `grafana/dashboards/tripilot_dashboard.json` with the command
above. The datasource UID is `tripilot-postgres` in both the provider and all
six dashboard panels. The two pie panels use named category fields so
multiple relevance labels or feedback ratings remain separate slices.

## Synchronize Grafana definitions

**Script names:** `k8s/sync-grafana.sh` is the helper included in this repository.
The separate `tripilot-grafana-sync-v2.sh` shown in README Figure 10z is a
standalone installer: it copies four Grafana files into the chosen project and
then runs this helper. They are different scripts, not a renamed file. A current
checkout already contains the permanent definitions and does not need that
standalone installer; use the repository helper below when synchronization is needed.

For an existing deployment in `kind-tripilot-cluster`, synchronize the
committed dashboard, datasource/provider ConfigMaps, and Grafana manifest.
The script validates both named-category transformations before applying
resources, waits for the Grafana rollout, and compares the mounted dashboard
with the source. It does not write conversation or feedback records and does
not restart the app, PostgreSQL, or Elasticsearch.

Stop the existing Grafana port-forward with Ctrl+C first. Grafana may replace
its local login/session state when the pod is replaced; log in again if prompted.

```bash
bash k8s/sync-grafana.sh  # synchronize only Grafana resources in the dedicated local cluster
kubectl --context=kind-tripilot-cluster --namespace=default port-forward svc/tripilot-grafana 3000:3000  # reconnect and keep this terminal running
```

Open `/d/tripilot-monitoring` in Grafana and hard-refresh the page. Confirm that
relevance labels and both feedback directions appear as separate categories
and match the app's Monitoring totals for the same observation time.

## Teardown and return to Compose

Stop the port-forward commands with Ctrl+C before freeing the cluster and
reusing the same host ports. Deleting this development cluster removes its
Kubernetes telemetry; it does not delete the retained Compose volume.

```bash
kind delete cluster --name tripilot-cluster  # remove only the dedicated local cluster and its ephemeral data
docker compose start                       # resume the retained Compose stack and its existing PostgreSQL records
```
