#!/usr/bin/env python3
"""Read-only pre-push checks for TripPilot's first import or later monorepo updates.

Run from the llm-zoomcamp repository root AFTER staging the intended changes:
    python3 Capstone3-tripilot/publishing/check_staged.py

This is a basic safety check, not a complete secret scanner or a code review.
It never changes Git's index, files, branches, remotes, or credentials.
"""
from pathlib import Path, PurePosixPath
import fnmatch
import re
import subprocess
import sys

PROJECT = "Capstone3-tripilot"
WORKFLOW = ".github/workflows/tripilot-ci.yml"
REQUIRED = {
    "README.md", ".gitignore", ".env.example", "app.py", "requirements.txt",
    "pyproject.toml", "Dockerfile", "docker-compose.yml", "Makefile",
    "data/reviews_snapshot.json", "data/hotels_snapshot.json",
    "data/ground_truth_qa.json", "data/city_costs.json",
    "data/routes_extract.csv", "data/openflights_extract.csv",
    "data/kaggle_hotel_reviews_extract.csv", "data/transcripts.txt",
    "data/audio/barcelona_beach_city_break.mp3",
    "data/audio/paris_vs_lyon_briefing.mp3",
    "data/audio/eastern_europe_value_briefing.mp3",
    "evaluation_results/retrieval_eval.json", "evaluation_results/rag_eval.json",
    "evaluation_results/selected_retriever.json",
    "grafana/dashboards/tripilot_dashboard.json", "k8s/05-grafana.yaml",
    "k8s/06-grafana-config.yaml", "k8s/sync-grafana.sh",
    "publishing/check_staged.py", "publishing/tripilot-ci.yml",
}
DENIED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".cache",
    ".mypy_cache", ".ruff_cache", ".terraform", "node_modules",
    "duckdb_data", ".streamlit-secrets",
}
DENIED_NAMES = {
    "secrets.toml", ".git-credentials", ".netrc", "credentials.json",
    "id_rsa", "id_ed25519", ".DS_Store",
}
DENIED_PATTERNS = (
    "*.pyc", "*.pyo", "*.db", "*.db-*", "*.sqlite", "*.sqlite3",
    "*.sqlite-*", "*.sqlite3-*", "*.duckdb", "*.duckdb.*", "*.tfstate*",
    "*.tfvars", "*.tfvars.json", "*.pem", "*.key", "*.p12", "*.pfx",
    "*.zip", "*.tar", "*.tar.gz", "*.tgz",
)
TOKEN_PATTERNS = (
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{24,}"),
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
)


def git(*args):
    return subprocess.check_output(["git", *args])


def fail(message):
    print(f"[publish] STOP: {message}", file=sys.stderr)
    raise SystemExit(1)


def forbidden(path):
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if any(part in DENIED_DIRS for part in parts):
        return True
    if name in DENIED_NAMES or (name.startswith(".env") and name != ".env.example"):
        return True
    if any(fnmatch.fnmatch(name, pattern) for pattern in DENIED_PATTERNS):
        return True
    return "/data/normalized/" in path or name in {"index_cache.json", "query_log.jsonl"}


def main():
    top = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if Path.cwd().resolve() != top:
        fail("Run this check from the llm-zoomcamp repository root.")
    changed = [p.decode() for p in git("diff", "--cached", "--name-only", "--no-renames", "-z").split(b"\0") if p]
    if not changed:
        fail("Nothing is staged.")
    outside = [p for p in changed if not (p.startswith(PROJECT + "/") or p == WORKFLOW)]
    if outside:
        fail("Unrelated paths are staged: " + ", ".join(outside))

    entries = {}
    for raw in git("ls-files", "--stage", "-z", "--", PROJECT, WORKFLOW).split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode, oid, stage = metadata.decode().split()
        path = raw_path.decode()
        if stage != "0":
            fail(f"Unresolved merge entry: {path}")
        if mode not in {"100644", "100755"}:
            fail(f"Non-regular file or nested repository: {path} (Git mode {mode})")
        if forbidden(path):
            fail(f"Runtime data, credentials, cache, or archive is staged: {path}")
        entries[path] = oid

    required = {f"{PROJECT}/{name}" for name in REQUIRED} | {WORKFLOW}
    missing = sorted(required - entries.keys())
    if missing:
        fail("Required publication files are missing from Git's index: " + ", ".join(missing))

    blobs = {}
    for path, oid in entries.items():
        size = int(git("cat-file", "-s", oid))
        if size > 50 * 1024 * 1024:
            fail(f"File exceeds this project's 50 MiB review limit: {path}")
        data = git("cat-file", "blob", oid)
        blobs[path] = data
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in TOKEN_PATTERNS):
            fail(f"Possible credential in {path}; inspect privately. The value was not printed.")

    if blobs[WORKFLOW] != blobs[f"{PROJECT}/publishing/tripilot-ci.yml"]:
        fail("The root CI workflow differs from its TripPilot template. Review and keep both in sync.")
    readme = blobs[f"{PROJECT}/README.md"].decode()
    image_refs = re.findall(r"!\[.*?\]\((docs/images/[^)]+)\)", readme)
    absent_images = [ref for ref in image_refs if f"{PROJECT}/{ref}" not in entries]
    if absent_images:
        fail("README images missing from Git's index: " + ", ".join(absent_images))

    print(f"[publish] Staged scope is limited to {PROJECT}/ and {WORKFLOW}.")
    print(f"[publish] Required source/data files and {len(image_refs)} README image references are present.")
    print("[publish] No nested Git repository, excluded runtime files, oversized files, or obvious token patterns found.")
    print("[publish] Basic checks passed. Still review the staged diff manually before committing or pushing.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"Git command failed with exit code {exc.returncode}; no changes were made.")
