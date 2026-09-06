# TripPilot on Fly.io

**Cloud deployment is deferred in Step 11; no cloud-deployment bonus is claimed for the current submission.** This optional guide is retained for future use. It prepares a single-Machine Fly.io demonstration, not a highly available production service. GCP/Terraform and Render remain other optional alternatives.

## Cost checkpoint — read before deploying

**Fly.io is not an ongoing free hosting tier.** Its free trial provides **2 total VM hours or 7 days of access, whichever comes first**. Trial Machines automatically stop after running for 5 minutes. Exhausting the trial stops the apps until a payment method is added. **Adding a card ends the trial and starts usage billing immediately.** Check your organization's actual Trial Status, credits, and billing terms before creating resources. [2](https://fly.io/docs/about/free-trial/)

For the configuration in this repository, the published `iad` prices checked on **2026-09-06** give this illustrative continuously-running estimate:

| Resource | Planned size | Approximate charge |
|---|---|---:|
| App Machine | 1 shared CPU, 1 GB RAM, running for 30 days | USD 5.70 |
| Persistent volume | 1 GB provisioned | USD 0.15 per month |
| Compute + volume subtotal | One Machine and one volume | **About USD 5.85** |

This is **not a fixed monthly price or a spending cap**. Runtime, region, traffic, snapshots, stopped-Machine root filesystem storage, other resources, and taxes can affect the bill. Volumes are billed while provisioned, even when detached or their Machine is stopped. Recheck the official pricing before deploying. [4](https://fly.io/docs/about/pricing/)

Auto-stop can lower idle compute usage, but it does not make hosting free or cap spending. Active Streamlit browser connections can keep the service busy; close unused tabs. Check the current-month bill in Fly's dashboard regularly. Do not assume credits or allowances limit your bill. [10](https://fly.io/docs/about/cost-management/)

**If your budget must remain USD 0, do not add a payment card or rely on Fly.io for ongoing peer-review hosting.** A short trial is useful for testing, but it can expire before reviewers visit the app. Choose an ongoing free-hosting alternative instead of assuming this guide is free.

## Deployment shape and data boundaries

- One `shared` CPU / 1 GB app Machine in `iad`, using the existing Dockerfile and Streamlit port **8501**.
- `--ha=false` prevents the initial deploy from creating spare high-availability Machines. Keep this SQLite-based demo at **one Machine**; a Fly Volume is local storage, not a shared database across replicas.
- One **1 GB** volume, `tripilot_data`, mounted at `/data`. SQLite telemetry lives at `/data/tripilot_monitoring.db`; the JSONL query log lives beside it.
- Committed review/route snapshots and evaluation artifacts stay in the image under `/app`. The local retrieval index can be rebuilt from the committed snapshot at startup.
- Without LLM/API secrets, the deployed app uses the same labelled **offline mock**, heuristic judge, and snapshot flight tools. Do not describe this as a live LLM call. Model-provider charges, if live keys are later configured, are separate from Fly.io hosting charges.
- No PostgreSQL, Elasticsearch, or Grafana service is provisioned on Fly by this guide. The cloud Monitoring tab therefore reports **`sqlite`**, not `postgres`. Its new telemetry is separate from the verified Compose/Kind PostgreSQL records.
- Your existing local Kind cluster and its 12-query monitoring evidence are not modified by these Fly commands.
- Auto-stop/restart preserves the volume's database, but in-memory Streamlit sessions can reset. A single local volume is not a high-availability or complete backup strategy.

## Prerequisites

Use the Ubuntu machine from the walkthrough, with Docker running, `curl`, Bash, and a Fly.io account. Install the Fly CLI only if it is not already available. Download its installer outside the project, inspect it, then run it:

```bash
curl -fsSL https://fly.io/install.sh -o "$HOME/fly-install.sh"  # download Fly's official CLI installer without executing it
less "$HOME/fly-install.sh"               # review the downloaded script; press q to exit the viewer
bash "$HOME/fly-install.sh"               # install the reviewed CLI into your home directory
export PATH="$HOME/.fly/bin:$PATH"        # make the Fly CLI available in this terminal
fly version                              # record the installed CLI version
```

Official installation reference: <https://fly.io/docs/flyctl/install/>.

## First deployment

These commands are **optional future work**, not part of the current verification run. Review the cost checkpoint first. They create a **new, dedicated app**, one volume, and one app Machine. Do not run the creation commands repeatedly against an existing deployment. The example working directory is the project folder inside a clone named `llm-zoomcamp`; adjust only that local path if your clone has another name.

```bash
cd ~/Documents/llm-zoomcamp/Capstone3-tripilot                    # use the project root as Docker's build context
export PATH="$HOME/.fly/bin:$PATH"         # make the home-directory Fly CLI installation available
fly version                              # record the installed Fly CLI version
docker version                           # confirm the local Docker daemon is available for the image build
fly auth login                           # authenticate in the browser; do not paste tokens into the README
fly orgs list                            # list organization slugs and select the intended trial/billing organization
export FLY_ORG="YOUR_ORG_SLUG"             # replace with your chosen organization slug
export FLY_APP="tripilot-your-unique-name" # replace with a globally unique app name; retain it for every later command

# First deployment only: continue only after reviewing the account's trial status or accepting usage charges.
fly apps create "$FLY_APP" --org "$FLY_ORG"  # create a dedicated app; skip this command if that app already exists
fly volumes create tripilot_data --app "$FLY_APP" --region iad --size 1  # provision one 1 GB persistent volume; skip if it already exists
fly deploy --app "$FLY_APP" --config fly.toml --local-only --ha=false --wait-timeout 10m  # build locally and deploy without requesting spare app Machines

fly status --app "$FLY_APP"                # inspect the deployment and assigned public hostname
fly machine list --app "$FLY_APP"          # confirm this demo has exactly one app Machine
fly volumes list --app "$FLY_APP"          # confirm one tripilot_data volume in iad
fly checks list --app "$FLY_APP"           # confirm the configured HTTP health check passes
CLOUD_URL="https://${FLY_APP}.fly.dev"      # construct the public URL for the app name you actually deployed
printf '%s\n' "$CLOUD_URL"                 # print the real URL for the README and browser verification
curl -fsS --retry 5 --retry-delay 5 --retry-all-errors --max-time 60 "$CLOUD_URL/healthz" && echo  # verify public HTTPS health, allowing a cold start

# Open the printed URL, submit a request, inspect the citation/tool output, and record the visible model mode.
# Rate an answer and open Monitoring; this Fly deployment should report sqlite, not the local Kind postgres backend.
# Replace Option C's placeholder only after the URL works; never include payment details, API keys, or tokens in screenshots.
```

1. Choose a globally unique app name and your intended organization slug from `fly orgs list`. The commands pass `--app "$FLY_APP"`, overriding the example `app = "tripilot-app"` in `fly.toml`.
2. Create the dedicated app, then the 1 GB `tripilot_data` volume in `iad`.
3. Deploy with **`--local-only --ha=false`**: build with your local Docker daemon and do not request spare app Machines. Do not substitute a remote builder or provision a cloud database without reviewing its costs.
4. Confirm one app Machine, one volume, passing health checks, and the public HTTPS URL.
5. Open the app, submit a request, inspect the citation/tool output, rate an answer, and capture the cloud Monitoring tab. Capture the full browser address bar so the cloud origin is visible.

For an existing app, retain its name and organization, inspect its current Machines and volumes, and skip first-time creation. Updating with `fly deploy` does not justify creating another volume. If a command fails, stop and inspect the output rather than creating duplicate resources.

The CLI supports `--app` overrides, `--local-only`, and `--ha=false`; see <https://fly.io/docs/flyctl/deploy/> and <https://fly.io/docs/reference/configuration/>.

## Verification evidence to collect

- Fly CLI version and successful deployment output.
- `fly status`, `fly machine list`, `fly volumes list`, and `fly checks list` for the same app.
- Actual `https://<your-app-name>.fly.dev` URL and a successful `/healthz` response.
- Cloud-served cited answer and visible model mode.
- Feedback confirmation and Monitoring showing the **SQLite** backend and the cloud app's own totals.

A manifest or example URL is not proof of deployment. No Fly screenshot is recorded until the app has actually been deployed. Do not include payment details, access tokens, API keys, or secret values in screenshots or Git commits.

## Inspecting and maintaining the demo

With `FLY_APP` still set to the app you created:

```bash
fly status --app "$FLY_APP"               # inspect the selected app, not another project
fly machine list --app "$FLY_APP"         # confirm the current Machine count and state
fly volumes list --app "$FLY_APP"         # inspect the persistent volume and region
fly checks list --app "$FLY_APP"          # inspect the application health checks
fly logs --app "$FLY_APP" --no-tail       # print available logs once without leaving a live log stream open
```

Keep the public demo available for the review period only if you accept the associated usage charges. The repository's Docker Compose workflow remains the account-free way to reproduce the complete PostgreSQL/Grafana stack.

## Cleanup after review

First export any cloud telemetry you want to retain. Deleting the app is destructive; stopping a Machine is not equivalent to deleting billable storage. After cleanup, inspect the Fly dashboard for remaining resources and accrued charges. Existing usage is still payable. [4](https://fly.io/docs/about/pricing/)

```bash
fly apps list                            # confirm the exact app name before considering deletion
# fly apps destroy "$FLY_APP"             # DESTRUCTIVE: delete only this demo app and its associated data after backup and confirmation
```

The destroy command is deliberately commented out so copying this block cannot delete the app accidentally. Do not delete or recreate your local Kind cluster as part of Fly cleanup.
