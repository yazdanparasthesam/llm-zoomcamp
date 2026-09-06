# Step 12 — Publish TripPilot inside your existing Zoomcamp repository

**Destination repository:** <https://github.com/yazdanparasthesam/llm-zoomcamp>  
**Destination folder:** `Capstone3-tripilot`  
**Base and final submission branch:** `main`  
**Working branch:** `add-capstone3-tripilot`  
**Cloud deployment:** Step 11 is deferred; no cloud-deployment bonus is claimed.

This is a **folder import into an existing repository**, not a new standalone Git repository. The original TripPilot development history must not replace your Zoomcamp history. The prepared `tripilot-capstone3-upload.zip` contains the current project, the corrected Grafana files, all recorded screenshots, and a root-level GitHub Actions workflow. It contains no `.git` directory, local environment, runtime database, private API keys, or the one-time Grafana installer.

**Publication is pending.** These instructions do not mean anything has already been pushed to your GitHub account.

## 1. Rules that protect the existing repository

1. **Clone the existing repository.** Do not run `git init` in `~/Documents/tripilot` and point that independent history at the Zoomcamp remote.
2. **Use exactly `Capstone3-tripilot`.** Put `app.py`, `README.md`, `data/`, and the other project files directly inside it. Do not create `Capstone3-tripilot/tripilot/` or a nested `.git` directory/submodule.
3. **Preserve the other coursework.** Do not replace the repository's root README, root `.gitignore`, `Capstone1-findocs-copilot`, `Capstone2-complaintradar`, or module folders.
4. **Stage only the two intended paths:** `Capstone3-tripilot/` and `.github/workflows/tripilot-ci.yml`. Do not use a blanket `git add .` or `git add -A` at the course-repository root.
5. **Include reproducibility evidence.** Keep the committed snapshots, canonical evaluation JSON, dependency lock, source, deployment configurations, `.env.example`, audio/transcripts, and README images. The prepared archive already includes them.
6. **Exclude runtime and private material.** Do not commit `.env`, private keys, Streamlit/dlt secrets, virtual environments, caches, generated SQLite/DuckDB databases, query logs, Terraform state, or ZIP archives. `.gitignore` does not remove a secret that is already tracked; inspect staged files as well.
7. **No force pushes or destructive resets.** Do not use `git push --force`, `--mirror`, or `git reset --hard` to overcome an upload problem. If a command fails, stop and inspect it; your other capstones must remain intact.
8. **Use a branch and pull request.** Review the two-path change and CI result before merging into `main`.
9. **Use your own Git author identity.** Configure it for this clone only. Copy your verified or GitHub-provided no-reply email from GitHub Settings → Emails; do not use the assistant workspace's example identity.
10. **Keep authentication out of files.** Use your existing Git credential manager, SSH setup, or GitHub CLI browser login. Never put a token into a remote URL, screenshot, README, or chat.
11. **Use the final `main` hash for submission.** A working-branch hash or the assistant workspace's hash is not the merged monorepo submission hash.

## 2. Expected layout

```text
llm-zoomcamp-tripilot-publish/        # a fresh local clone; its name is only local
├── .git/                           # the ONE repository's Git metadata
├── .gitignore                      # existing repository file: unchanged
├── README.md                       # existing repository README: unchanged
├── .github/
│   └── workflows/
│       └── tripilot-ci.yml         # new root workflow; scoped to Capstone3-tripilot
├── 01-agentic-rag/                 # existing coursework: unchanged
├── ...
├── Capstone1-findocs-copilot/       # unchanged
├── Capstone2-complaintradar/        # unchanged
└── Capstone3-tripilot/
    ├── README.md
    ├── .gitignore
    ├── .env.example
    ├── app.py
    ├── requirements.txt
    ├── data/
    ├── evaluation_results/
    ├── docs/
    ├── grafana/
    ├── k8s/
    ├── publishing/
    │   ├── check_staged.py
    │   └── tripilot-ci.yml         # source template for the root workflow
    └── ...
```

GitHub Actions discovers workflow files in the **repository-root** `.github/workflows/` directory. The project's existing `.github/workflows/ci.yml` is retained for standalone use, but it will not run when nested inside `Capstone3-tripilot`. The supplied root `tripilot-ci.yml` sets `working-directory: Capstone3-tripilot`, filters its push/PR paths, uses Python 3.11 and pinned dependencies, and does not receive model/API secrets. Keep that root file synchronized with its template inside `publishing/`.

## 3. Before running the commands

- Save **`tripilot-capstone3-upload.zip`** in `~/Documents`. If your browser saves to Downloads, move it to Documents or edit the `ARCHIVE` line below.
- Use the **new publication archive**, not the original early `tripilot.zip` or a documentation-only ZIP.
- The fresh clone path `~/Documents/llm-zoomcamp-tripilot-publish` must not already exist. If it exists, do not delete it blindly or re-run the initial import; inspect its branch, remote, and uncommitted work first.
- You need Git, Python 3, and `unzip`. No running cloud service is required.
- Make sure you can authenticate to GitHub for a push. Public cloning does not test write authentication.

If the GitHub CLI is already installed and you want browser-based HTTPS authentication, these optional commands configure it without putting a token in a URL:

```bash
gh auth login --hostname github.com --git-protocol https --web  # sign in through GitHub's browser/device flow
gh auth setup-git                          # let Git use the CLI's credential helper
```

Do not share the browser/device code or token. If you use a different credential manager or SSH, keep that existing authentication method instead. GitHub account passwords are not HTTPS Git push credentials.

## 4. Import, review, publish, and verify

The command block runs inside a subshell so a failed check stops the workflow without closing your outer Ubuntu terminal. It deliberately pauses before committing and after pushing. **Read the instructions printed by each pause.** No existing course file is overwritten.

```bash
(                                           # isolate variables and error handling from the outer terminal
set -euo pipefail                            # stop this workflow on the first failed command
REPO_URL="https://github.com/yazdanparasthesam/llm-zoomcamp.git"  # select the existing repository, not a new TripPilot repository
PUBLISH_DIR="$HOME/Documents/llm-zoomcamp-tripilot-publish"  # use a fresh sibling clone, leaving your working project untouched
ARCHIVE="$HOME/Documents/tripilot-capstone3-upload.zip"  # select the current prepared publication archive

test -f "$ARCHIVE"                           # stop if the downloaded publication archive is missing
test ! -e "$PUBLISH_DIR" && test ! -L "$PUBLISH_DIR"  # refuse to overwrite an existing folder or symbolic link
git clone --branch main --single-branch "$REPO_URL" "$PUBLISH_DIR"  # retain the existing main branch and repository history
cd "$PUBLISH_DIR"                            # perform all subsequent Git operations at the course-repository root
test "$(git remote get-url origin)" = "$REPO_URL"  # verify the intended remote before changing anything
test -z "$(git status --porcelain)"           # require a clean fresh clone
git switch -c add-capstone3-tripilot          # isolate the new capstone in a reviewable branch

git config user.name "yazdanparasthesam"      # set the author name only for this clone
read -r -p 'Your verified or GitHub no-reply author email: ' AUTHOR_EMAIL  # enter your own author email locally, not in chat
test -n "$AUTHOR_EMAIL"                      # stop if no author email was supplied
git config user.email "$AUTHOR_EMAIL"        # configure the author email without changing global Git settings

test ! -e Capstone3-tripilot && test ! -L Capstone3-tripilot  # refuse to replace an existing capstone folder
test ! -L .github && test ! -L .github/workflows  # refuse to extract through a workflow-directory symbolic link
test ! -e .github/workflows/tripilot-ci.yml && test ! -L .github/workflows/tripilot-ci.yml  # preserve any pre-existing workflow with that name
unzip -l "$ARCHIVE"                          # inspect the archive: only Capstone3-tripilot/ and the one root CI file
unzip -n "$ARCHIVE"                          # extract the new files without overwriting existing repository files
git status --short                          # inspect the imported paths before staging

git add -- Capstone3-tripilot .github/workflows/tripilot-ci.yml  # stage only the new project and its root-level CI workflow
python3 Capstone3-tripilot/publishing/check_staged.py  # check scope, required files, image references, nested Git, and obvious sensitive files
git diff --cached --check                    # reject whitespace errors in the staged changes
git diff --cached --stat                     # inspect the staged change summary
git diff --cached --name-status              # verify no older coursework is modified or deleted
git diff --cached                            # review the staged text; do not screenshot any private values
read -r -p 'After reviewing the staged diff, type PUBLISH to continue: ' APPROVAL  # pause for your explicit publication approval
test "$APPROVAL" = PUBLISH                   # stop unless you approved the reviewed changes
git commit -m "feat: add Capstone3 TripPilot with verified local deployment"  # record the project without claiming a cloud deployment
git push -u origin add-capstone3-tripilot     # push the feature branch without rewriting main or other project history
printf '%s\n' 'https://github.com/yazdanparasthesam/llm-zoomcamp/compare/main...add-capstone3-tripilot?expand=1'  # open this URL to create the pull request

# In GitHub: create the PR into main, inspect Files changed, wait for TripPilot CI, then merge it.
read -r -p 'After the PR is merged into main, type MERGED to verify the submission: ' MERGE_STATUS  # wait for the actual GitHub merge
test "$MERGE_STATUS" = MERGED                # do not claim a main-branch submission before merging
git switch main                             # return to the repository's submission branch
git pull --ff-only origin main              # download the merged commit without creating a local merge
LOCAL_SHA="$(git rev-parse HEAD)"            # capture the full main-branch commit hash
REMOTE_SHA="$(git ls-remote origin refs/heads/main | cut -f1)"  # read the current GitHub main hash
test "$LOCAL_SHA" = "$REMOTE_SHA"            # confirm the local and remote submission revisions match
printf 'Local main:  %s\nRemote main: %s\n' "$LOCAL_SHA" "$REMOTE_SHA"  # display both hashes for the verification screenshot
printf 'Pinned project URL: https://github.com/yazdanparasthesam/llm-zoomcamp/tree/%s/Capstone3-tripilot\n' "$LOCAL_SHA"  # identify the exact project folder at that commit
git status --short                          # show any remaining local changes; no output means clean
test -z "$(git status --porcelain)"          # enforce the clean-working-tree check
)                                           # return to the unchanged outer terminal environment
```

The pre-push helper is **read-only and limited**: it checks Git's staged scope, required project files, image paths, regular-file modes, selected runtime/credential filenames, basic token patterns, and a 50 MiB per-file review threshold. It is not a guarantee that every possible secret is absent. You must still review the staged diff yourself.

## 5. Screenshots and submission information

Capture:

1. The staged summary showing `Capstone3-tripilot/` and the root CI file, without changes to earlier coursework.
2. The successful branch push and the PR's passing **TripPilot CI** check.
3. The merged GitHub folder at `main/Capstone3-tripilot`, with its rendered README.
4. The terminal's matching **full local/remote main hashes** and clean working-tree check.

After merging, the normal folder URL will be:

<https://github.com/yazdanparasthesam/llm-zoomcamp/tree/main/Capstone3-tripilot>

For the review form, use:

- **Repository URL:** `https://github.com/yazdanparasthesam/llm-zoomcamp`
- **Project path:** `Capstone3-tripilot`
- **Commit hash:** the full 40-character `main` hash printed by the commands, not an assistant workspace commit or an unmerged branch commit.
- **Pinned project URL:** the printed `tree/<full-hash>/Capstone3-tripilot` URL when a project-folder link is accepted.

**Adding these screenshots to the README creates another commit.** Publish that final documentation update and obtain the latest merged `main` hash again before submitting. A screenshot can document an earlier publication checkpoint; do not claim that its older hash is the final hash after more commits have been added.

## 6. If a command stops

- **Existing clone or destination folder:** do not delete it. Inspect its remote, branch, and status; use a separate update branch rather than importing over an existing project blindly.
- **Authentication failure:** fix GitHub authentication, return to the publication clone, and retry the push. Do not regenerate the project, reinitialize Git, or include a token in the remote URL.
- **Rejected branch push:** inspect the remote branch; do not force-push over changes you have not reviewed.
- **Staged-scope or secret warning:** inspect the named file privately and unstage only the unintended path. Rotate an exposed real credential if it was published.
- **CI failure:** read the failing job; do not merge merely to obtain a screenshot. The workflow runs in a disposable GitHub checkout and does not write evaluation artifacts back to your branch.
- **Hash mismatch after merge:** fetch/pull the latest `main` again and verify; another commit may have arrived since the previous check.

Nothing in this publication workflow stops your local Kind cluster, deletes its PostgreSQL data, or deploys a paid cloud resource.
