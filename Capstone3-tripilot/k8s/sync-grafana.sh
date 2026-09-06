#!/usr/bin/env bash
# Synchronize only TripPilot's Grafana resources in the dedicated local Kind cluster.
# Stop the Grafana port-forward before running; reconnect it when this command finishes.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
CONTEXT=kind-tripilot-cluster
NAMESPACE=default
K=(kubectl --context="$CONTEXT" --namespace="$NAMESPACE")
DASHBOARD=grafana/dashboards/tripilot_dashboard.json

command -v kubectl >/dev/null || { echo 'kubectl is required.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'python3 is required.' >&2; exit 1; }
command -v cmp >/dev/null || { echo 'cmp is required.' >&2; exit 1; }

# Validate the source definition before making any API changes.
python3 - "$DASHBOARD" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
d = json.loads(p.read_text(encoding='utf-8'))
if d.get('uid') != 'tripilot-monitoring' or len(d.get('panels', [])) != 6:
    raise SystemExit('Expected the six-panel tripilot-monitoring dashboard.')
for panel_id, category in ((3, 'relevance'), (4, 'feedback')):
    panel = next((p for p in d['panels'] if p.get('id') == panel_id), None)
    expected = {
        'id': 'rowsToFields',
        'options': {'mappings': [
            {'fieldName': category, 'handlerKey': 'field.name'},
            {'fieldName': 'n', 'handlerKey': 'field.value'},
        ]},
    }
    if panel is None or panel.get('transformations') != [expected]:
        raise SystemExit(f'Panel {panel_id} needs its named-category transformation.')
print(f'[grafana] Source dashboard validated: version {d.get("version")}, six panels, both category mappings.')
PY

# Scope all operations to this existing local deployment; do not recreate the cluster.
BEFORE="$("${K[@]}" get deployment tripilot-grafana -o jsonpath='{.spec.template}')"
"${K[@]}" apply -f k8s/06-grafana-config.yaml
"${K[@]}" create configmap tripilot-grafana-dashboard \
  --from-file="tripilot_dashboard.json=$DASHBOARD" \
  --dry-run=client -o yaml | "${K[@]}" apply -f -
"${K[@]}" apply -f k8s/05-grafana.yaml
AFTER="$("${K[@]}" get deployment tripilot-grafana -o jsonpath='{.spec.template}')"

# A changed pod template already starts a rollout; otherwise restart to load the ConfigMaps now.
if [[ "$BEFORE" == "$AFTER" ]]; then
  "${K[@]}" rollout restart deployment/tripilot-grafana
fi
"${K[@]}" rollout status deployment/tripilot-grafana --timeout=300s

# Confirm the provisioning files and the exact dashboard bytes in the replacement pod.
"${K[@]}" exec deployment/tripilot-grafana -- \
  ls -l /etc/grafana/provisioning/dashboards/dashboards.yaml \
        /etc/grafana/provisioning/datasources/datasources.yaml \
        /var/lib/grafana/dashboards/tripilot_dashboard.json
"${K[@]}" exec deployment/tripilot-grafana -- \
  cat /var/lib/grafana/dashboards/tripilot_dashboard.json | cmp -s "$DASHBOARD" -
echo '[grafana] Mounted dashboard matches the validated source exactly.'
echo '[grafana] PostgreSQL records were not modified; only Grafana resources were synchronized.'
echo 'Reconnect the Grafana port-forward, log in if prompted, and hard-refresh the dashboard.'
echo 'kubectl --context=kind-tripilot-cluster --namespace=default port-forward svc/tripilot-grafana 3000:3000'
