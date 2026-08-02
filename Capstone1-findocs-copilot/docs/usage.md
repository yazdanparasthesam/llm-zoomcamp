# 📖 FinDocs Copilot — Usage Walkthrough & User Guide

This guide explains how to interact with **FinDocs Copilot**, explore citations, submit user feedback, and monitor live telemetry in Grafana and Streamlit.

---

## 1. Using the Streamlit Web Interface (`app.py`)

When you open **http://localhost:8501**, you are greeted by three main tabs:
1. **💬 Financial Chat & Citations**
2. **📈 Monitoring & User Feedback**
3. **🔬 Module Evaluation Metrics**

### Step 1: Select or Type a Financial Question
- Use the left sidebar to filter by a specific company ticker (e.g., `NVDA`, `AAPL`, `MSFT`, `TSLA`, `GOOGL`) or leave as **All Companies**.
- Choose your **Retrieval Method**:
  - `🌟 Hybrid + Re-ranking (Best Practice)`: Combines BM25 keywords + Cosine semantic similarity with financial section boosting.
  - `🔗 Hybrid Search (BM25 + Cosine RRF)`: Reciprocal Rank Fusion of keyword and vector search.
  - `📝 Text Search (BM25 Keyword)`: Pure keyword search.
  - `🧠 Vector Search (Dense Cosine)`: Pure dense vector similarity.
- Type your question in the text box or pick one from the **💡 Try Sample Financial Queries** dropdown in the sidebar.

### Step 2: Analyze the AI Analyst Response & Citations
- Click **Submit Question**.
- View the synthesized **AI Analyst Assessment**.
- Check the **LLM-as-a-Judge Relevance Badge**:
  - 🟢 **RELEVANT**: Directly answers the question using facts from the SEC filing.
  - 🟡 **PARTIALLY_RELEVANT**: Touches on the topic but may miss key figures.
  - 🔴 **NON_RELEVANT**: Does not answer the question or lacks context.
- Expand **📚 View Cited SEC 10-K & Earnings Call Context Chunks** to verify the underlying SEC text, section name, and `chunk_id`.

### Step 3: Submit User Feedback (+1 / -1)
- Below the citations, click **👍 Yes (+1)** or **👎 No (-1)** to indicate whether the response was helpful.
- This feedback is logged instantly into the PostgreSQL/SQLite database (`feedback` table) and updates the monitoring dashboard in real time.

---

## 2. Exploring Live Monitoring Statistics

### Option A: In-App Streamlit Monitoring Tab
Navigate to the **📈 Monitoring & User Feedback** tab to see:
- Total Logged Queries
- Average Response Latency (ms)
- Average Relevance Score (%)
- Positive vs. Negative User Feedback breakdown
- Relevance distribution and queries by ticker symbol

### Option B: Pre-Provisioned Grafana Dashboard (Port 3000)
When running via Docker Compose, open **http://localhost:3000**:
- Login with username `admin` and password `admin`.
- Open **FinDocs Copilot — RAG Monitoring Dashboard** from the dashboards list.
- Explore 6 interactive charts tracking time series query volume, average latency, relevance labels, and user feedback ratios.

---

## 3. Running Automated Peer Review Evaluations

To inspect the retrieval and RAG evaluation tables from the command line:

### Run Retrieval Evaluation:
```bash
python -m src.eval_retrieval
```
Outputs a table comparing BM25, Cosine, Hybrid RRF, and Hybrid+Rerank across both `doc_id` and `chunk_id` HitRate@5 and MRR@5.

### Run LLM Output Evaluation:
```bash
python -m src.eval_rag
```
Outputs a table comparing **Analyst**, **Concise Auditor**, and **Strategic Advisor** prompt templates using LLM-as-a-Judge relevance percentages (`RELEVANT`, `PARTIAL`, `NON_REL`).
