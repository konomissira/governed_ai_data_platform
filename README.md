# 🏛️ Governed Enterprise AI Data Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)
![React](https://img.shields.io/badge/React-18.2-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![Google Cloud](https://img.shields.io/badge/GCP-Vertex%20AI%20%7C%20BigQuery-4285F4.svg)
![dbt](https://img.shields.io/badge/dbt-1.7.0-orange.svg)

An enterprise-grade, full-stack AI platform that allows users to ask natural language questions about ERP data and receive accurate, governed KPI dashboards in return.

Unlike dangerous **Text-to-SQL** implementations that risk data hallucinations, SQL injection, and runaway database costs, this architecture uses an **Intent-Routing (Parameter Extraction) pattern**. The LLM never writes SQL it only extracts parameters, which are then passed securely to pre-written, governed BigQuery models built with dbt.

---

## 📸 Demo

> _Type a natural language question → Vertex AI extracts intent → BigQuery returns governed data → KPI cards render instantly._

---

## ✨ Business Value & Architecture

Enterprise data must be **deterministic**. This platform guarantees accuracy by keeping the AI completely separate from SQL execution.

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
│          "What is our revenue for GB01 in GBP?"         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              React + Nginx  (Port 80)                    │
│         ChatGPT-style UI with KPI Dashboard             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            FastAPI Backend  (Port 8000)                  │
│                  Guardrail Check                         │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────┐  ┌───────────────────────────────┐
│   Google Vertex AI   │  │       Google BigQuery          │
│  Gemini 2.0 Flash    │  │   dbt Gold Layer (Governed)    │
│ Parameter Extraction │  │   fct_sales_orders table       │
└──────────────────────┘  └───────────────────────────────┘
```

### How It Works

1. **User Input** : A user asks a natural language question via the React dashboard (e.g., _"What is our revenue for GB01 in GBP?"_).

2. **AI Guardrail & Intent Routing** : The FastAPI backend passes the prompt to **Google Vertex AI (Gemini)**. The AI evaluates whether the question is supported, then extracts the exact parameters (`sales_org: GB01`, `currency: GBP`). Unsupported questions are blocked before they ever touch BigQuery.

3. **Governed Data Execution** : The extracted parameters are injected into a **pre-written, parameterised SQL query** running against the dbt-modelled Gold layer in BigQuery. The LLM never generates SQL.

4. **Deterministic UI** : The data flows back to the React frontend and renders as beautiful, accurate KPI cards. Zero hallucinations. Zero SQL injection risk.

---

## 🛡️ Why Not Text-to-SQL?

|                    | Text-to-SQL          | This Platform                     |
| ------------------ | -------------------- | --------------------------------- |
| SQL Generation     | ✅ LLM writes SQL    | ❌ LLM never touches SQL          |
| SQL Injection Risk | ⚠️ High              | ✅ Architecturally impossible     |
| Hallucination Risk | ⚠️ High              | ✅ Zero data is deterministic     |
| Cost Control       | ⚠️ Unbounded queries | ✅ Pre-defined query scope        |
| Auditability       | ⚠️ Hard to audit     | ✅ Every query is governed by dbt |

---

## 🛠️ Tech Stack

### Data Layer

- **Python & Pandas** : SAP ERP data generation pipeline (VBAK/VBAP)
- **Google BigQuery** : Enterprise cloud data warehouse (EU region)
- **dbt 1.7** : Medallion Architecture (Bronze → Silver → Gold) with 17 automated governance tests

### Backend

- **Python & FastAPI** : High-performance, async API framework
- **Google Vertex AI (Gemini 2.0 Flash)** : LLM intent routing and parameter extraction
- **Pydantic** : Request/response validation

### Frontend

- **React & Vite** : Lightning-fast frontend tooling
- **Tailwind CSS & Lucide Icons** : Modern, responsive UI components
- **Nginx** : Multi-stage Docker build for serving compiled static assets with API proxying

### Infrastructure

- **Docker & Docker Compose** : Full-stack containerisation for one-command deployment

---

## 📁 Project Structure

```
governed_entreprise_ai_data_platform/
├── data_generation/          # Branch 1 SAP ERP data pipeline
│   ├── generate_sap_data.py  # Generates VBAK/VBAP mock SAP data → BigQuery
│   └── requirements.txt
│
├── dbt_cortex_project/       # Branch 2 dbt Medallion Architecture
│   ├── models/
│   │   ├── bronze/           # Raw source references (ephemeral)
│   │   ├── silver/           # Cleaned SAP data (views)
│   │   └── gold/             # Business-ready aggregations (tables)
│   ├── dbt_project.yml
│   └── profiles.yml          # gitignored contains credentials
│
├── backend/                  # Branch 3 Governed AI Backend
│   ├── main.py               # FastAPI app with CORS and lifespan handler
│   ├── ai_router.py          # Vertex AI intent extraction + guardrails
│   ├── database.py           # BigQuery parameterised query execution
│   └── requirements.txt
│
├── frontend/                 # Branch 5 React Frontend
│   ├── src/
│   │   └── App.jsx           # Chat UI with KPI dashboard cards
│   ├── nginx.conf            # Nginx config with API proxy
│   └── Dockerfile            # Multi-stage build (Node → Nginx)
│
├── Dockerfile                # Backend container
├── docker-compose.yml        # Full-stack orchestration
├── .env                      # gitignored GCP_PROJECT_ID
└── gcp-service-account-key.json  # gitignored GCP credentials
```

---

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose installed
- A Google Cloud Project with **Vertex AI API** and **BigQuery API** enabled
- A GCP Service Account Key with the following IAM roles:
    - `BigQuery Data Viewer`
    - `BigQuery Job User`
    - `Vertex AI User`

### 1. Clone the Repository

```bash
git clone https://github.com/konomissira/governed_ai_data_platform.git
cd governed_ai_data_platform
```

### 2. Add Your GCP Credentials

Place your GCP service account JSON key in the project root:

```bash
# Ensure it is named exactly:
gcp-service-account-key.json
```

### 3. Create the `.env` File

```bash
# Create a .env file in the project root:
GCP_PROJECT_ID=your-actual-gcp-project-id
```

### 4. Launch the Full Stack

Start the entire platform backend and frontend with a single command:

```bash
docker-compose up --build
```

### 5. Open the Platform

| Service              | URL                        |
| -------------------- | -------------------------- |
| React Dashboard      | http://localhost           |
| FastAPI Swagger Docs | http://localhost:8000/docs |

---

## 💬 Example Queries

Try these in the UI:

```
What is our total revenue in GBP?
Show me sales for GB01
What is our revenue for US01 in USD?
Show me total orders for DE01
```

### Guardrail Tests

These will be politely blocked by the AI guardrail:

```
What is the weather in London?
Show me employee salaries
What is the stock price of Apple?
```

---

## 🛡️ AI Guardrails

This system includes strict LLM guardrails. If a user asks about unsupported dimensions (e.g., specific products, employee data) or completely unrelated topics (e.g., the weather), the AI router sets `is_supported_question: false` and the API returns an HTTP `400` response, which the UI handles gracefully with a clear error message.

**Guardrail logic is fail-safe by design** : if the Vertex AI call fails for any reason, `is_supported_question` defaults to `false`, ensuring nothing reaches BigQuery.

---

## 🤝 API-First / Headless Architecture

The backend API is completely frontend-agnostic. You can connect this governed data API to any frontend:

- Streamlit
- Vue or Angular
- Custom mobile application
- Internal BI tools

The FastAPI Swagger documentation at `http://localhost:8000/docs` provides a full interactive API reference.

---

## 📄 Licence

MIT

---

## 🔧 Engineering Decisions & Real-World Debugging

Building this platform on real GCP infrastructure surfaced three important engineering challenges. They are documented here because understanding how to debug cloud systems is as valuable as writing the code itself.

### 🌐 1. The DNS Block (gRPC Resolver Issue)

**Problem:** On macOS, the Vertex AI SDK uses the C-ares DNS resolver by default for gRPC connections. This caused `503 DNS resolution failed` errors when trying to reach `europe-west2-aiplatform.googleapis.com`, even though the endpoint was reachable via `curl`.

**Fix:** Override the gRPC DNS resolver to use the native system resolver:

```bash
export GRPC_DNS_RESOLVER=native
```

This is included in `docker-compose.yml` as a permanent environment variable so the containerised app never hits this issue.

---

### 🌍 2. The Region Lock (404 Model Not Found)

**Problem:** Vertex AI requests were initially routed to the London data centre (`europe-west2`) to keep everything in the EU. However, the specific Gemini model version (`gemini-2.0-flash-001`) was not yet fully rolled out in that region, returning a `404 Publisher Model not found` error.

**Fix & Architectural Trade-off:** AI API calls were re-routed to Google's primary AI hub (`us-central1`). BigQuery data remains in the EU region.

> This is a well-established pattern in Enterprise Architecture keep your **Data Warehouse in Europe** for GDPR compliance, but route **AI API calls to the US** for model availability. Your underlying business data never leaves Europe. Only the natural language question and the extracted JSON parameters cross regions never the actual data.

---

### 📦 3. The SDK Version Conflict

**Problem:** The Python SDK version pinned in `requirements.txt` (`google-cloud-aiplatform==1.42.1`) was older than the features being called. Specifically, the `system_instruction` parameter in `GenerativeModel()` was introduced in a later SDK version, causing an unexpected `TypeError` at startup.

**Fix:** The `system_instruction` was moved out of the model constructor and prepended directly to the user prompt instead a backwards-compatible pattern that works across SDK versions:

```python
prompt = f"{self.system_instruction}\n\nUser Question: {user_question}\nOutput JSON:"
response = self.model.generate_content(prompt)
```

> **Key takeaway:** AI coding tools are powerful productivity boosters, but their training data is often months behind the latest cloud SDK releases. When the AI cannot resolve an SDK conflict, go back to basics read the official documentation and map the exact supported features to your pinned SDK version.
