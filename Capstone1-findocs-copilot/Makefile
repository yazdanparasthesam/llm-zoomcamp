# FinDocs Copilot — Makefile Automation

.PHONY: install ingest eval test run docker-up docker-down k8s-apply

install:
	pip install -r requirements.txt

ingest:
	python3 -m src.ingest

eval:
	python3 -m src.eval_retrieval
	python3 -m src.eval_rag

test:
	pytest tests/ -v

run:
	streamlit run app.py --server.port=8501

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

k8s-apply:
	kubectl apply -f k8s/
