# ComplaintRadar — Makefile Automation

.PHONY: install dlt-ingest ingest eval test run docker-up docker-down k8s-apply

install:
	pip install -r requirements.txt

dlt-ingest:
	PYTHONPATH=. python3 ingestion/cfpb_pipeline.py

ingest:
	PYTHONPATH=. python3 -m src.ingest

eval:
	PYTHONPATH=. python3 -m src.eval_retrieval
	PYTHONPATH=. python3 -m src.eval_rag

test:
	PYTHONPATH=. pytest tests/ -v

run:
	PYTHONPATH=. streamlit run app.py --server.port=8501

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

k8s-apply:
	kubectl apply -f k8s/
