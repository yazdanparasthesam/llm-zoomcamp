# TripPilot — one-command automation for peer reviewers
.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install pinned Python dependencies
	pip install -r requirements.txt

generate-data: ## Regenerate deterministic snapshot + ground truth (seeds 42/123)
	python3 data/generate_snapshot.py
	python3 data/generate_ground_truth.py

dlt-ingest: ## dlt extract+normalize -> DuckDB + data/normalized (uses committed snapshot)
	python3 ingestion/hotel_reviews_pipeline.py

ingest: ## Module-07 chunking + embeddings + optional ES mirror
	python3 -m src.ingest

audio: ## Regenerate multimodal audio briefings (needs network + gtts)
	python3 data/generate_audio.py

eval: eval-retrieval eval-rag ## Run both evaluations

eval-retrieval: ## 4 retrieval approaches, doc+chunk Hit@5/MRR@5, picks winner
	python3 -m src.eval_retrieval

eval-rag: ## LLM-as-a-Judge over 3 prompt strategies (negative control incl.)
	python3 -m src.eval_rag

test: ## Run the pytest suite (13 tests)
	python3 -m pytest tests/ -q

run: ## Launch the Streamlit copilot on :8501
	streamlit run app.py --server.address=0.0.0.0 --server.port=8501

init-db: ## Initialize telemetry DB (Postgres if up, else SQLite)
	python3 -m src.db

docker-up: ## Full stack: app + Elasticsearch + Postgres + Grafana
	docker compose up --build -d
	@echo "app: http://localhost:8501  grafana: http://localhost:3000 (admin/admin)"

docker-down: ## Stop and remove the stack
	docker compose down -v

k8s-apply: ## Deploy to a LOCAL Kind/Minikube cluster (see k8s/README-k8s.md)
	kubectl apply -f k8s/

k8s-delete: ## Remove the Kubernetes deployment
	kubectl delete -f k8s/ --ignore-not-found

clean: ## Remove generated caches (keeps committed snapshot + results)
	rm -f data/tripilot_monitoring.db data/query_log.jsonl
	rm -rf data/normalized data/index_cache.json data/tripilot.duckdb

.PHONY: help install generate-data dlt-ingest ingest audio eval eval-retrieval eval-rag test run init-db docker-up docker-down k8s-apply k8s-delete clean
