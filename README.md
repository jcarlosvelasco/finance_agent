# finance-agent — Automated Financial Analysis with AI

An **AI-powered financial research agent** that, given a stock ticker, autonomously validates the ticker, fetches fundamentals and news, performs sentiment analysis, and generates a comprehensive investment report — all running locally via Ollama with no external API costs for inference.

> **Why this project?** Financial research is time-consuming: you need to check financials, read news, gauge sentiment, and synthesize everything into a coherent view. This agent automates the entire pipeline end-to-end.

---

## Architecture

```
HTTP GET /generate_report?ticker=AAPL
         │
         ├─ Cache check ─────────────────────────────────────┐
         │  src/data/reports/AAPL.json                       │
         │  If exists AND modified today → return cached ✔   │
         └───────────────────────────────────────────────────┘
                        │ (cache miss)
                        ▼

              ┌─────────────────┐
              │   supervisor    │  yfinance — validates ticker exists
              └────────┬────────┘
                       │ valid_ticker
                       ▼
              ┌─────────────────┐
              │  fundamentals   │  yfinance tools (parallel):
              │                 │  get_stock_info + get_financials
              └────────┬────────┘
                       │ company_info
                       ▼
              ┌─────────────────┐
              │      news       │  Tavily search → LLM sentiment analysis
              └────────┬────────┘
                       │ sentiment + key_events
                       ▼
              ┌─────────────────┐
              │     report      │  LLM generates 7-section report
               └────────┬────────┘
                        │ report
                        ▼
               ┌─────────────────┐
               │      save       │  Caches JSON → src/data/reports/{TICKER}.json
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │    evaluate     │  LLM judge scores report (5 criteria)
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   END / return  │
               └─────────────────┘

Every step is traced in Langfuse (latency · tokens · errors per node). The evaluation node also sends quality scores (factual consistency, completeness, analytical depth, actionability, coherence) as Langfuse feedback scores.
```

---

## Engineering Decisions

**LangGraph StateGraph over sequential function calls**
The pipeline has clear stages with conditional routing (invalid ticker → early exit). LangGraph gives us explicit state transitions, error isolation per node, and a natural place to inject observability.

**`yfinance` for fundamentals over an external API**
Yahoo Finance data is free, requires no API key, and covers all the fields needed (price, PE, D/E, FCF, margins). The trade-off is that data is delayed by ~15 minutes — acceptable for research-grade analysis.

**Tavily for news search**
Purpose-built for LLM agents: returns structured results with relevance scores, supports topic filtering (`news` topic), and has a simple API. 1000 free queries/month.

**`gemma4:e2b-mlx` via Ollama**
Runs entirely on Apple Silicon at ~40 tokens/s with no API costs. MLX-optimized quantization fits in 16GB RAM. The mock fallback (`LLM_PROVIDER=mock`) enables CI testing without a GPU.

**Sentiment parsing with structured output**
The LLM returns JSON `{"sentiment": "...", "key_events": [...]}` rather than free text, making the result parseable and type-safe via Pydantic without function-calling support from the local model. Structured output is not working with the local model because it does not support it natively or because it is too small.

**LLM-as-judge for report quality evaluation**
After generation, a separate LLM call scores the report on 5 criteria (factual consistency, completeness, analytical depth, actionability, coherence). Scores are sent to Langfuse as feedback for tracking quality over time — no human reviewer needed for CI evaluation.

**File-based caching with mtime expiry**
Reports are cached as `{TICKER}.json` and invalidated by comparing file modification date to today — no cleanup script needed, no external cache service.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Pydantic + Uvicorn |
| Orchestration | LangGraph (StateGraph) |
| LLM | Ollama · gemma4:e2b-mlx |
| Financial Data | yfinance |
| News API | Tavily |
| Observability | Langfuse v2 |
| Infrastructure | Docker · Docker Compose |

---

## Project Structure

```
finance-agent/
├── src/
│   ├── api/
│   │   ├── main.py                    FastAPI app + /generate_report endpoint
│   │   └── schemas/
│   │       └── GenerateReportRequest.py   Pydantic request model
│   ├── graph/
│   │   ├── graph.py                   StateGraph definition + conditional edges
│   │   └── state.py                   TypedDict state (AnalysisState, CompanyInfo)
│   ├── nodes/
│   │   ├── supervisor.py              Validates ticker via yfinance
│   │   ├── fundamentals.py            Fetches stock info + financials in parallel
│   │   ├── news.py                    Tavily search + LLM sentiment analysis
│   │   ├── report.py                  Generates final report via LLM
│   │   ├── evaluate_report.py         LLM judge scores report quality
│   │   ├── save_report.py             Caches report to JSON + cache load logic
│   │   └── prompts.py                 SENTIMENT_PROMPT + REPORT_PROMPT + JUDGE_PROMPT
│   ├── shared/
│   │   └── llm.py                     LLM factory (ChatOllama or mock for CI)
│   ├── tools/
│   │   └── yfinance_tools.py          LangChain tools: get_stock_info, get_financials
│   ├── langfuse.py                    Langfuse client singleton
│   ├── settings.py                    Pydantic Settings (generator_model)
│   └── data/reports/                  Cached report JSON files
├── docker-compose.yml                 App + Langfuse + Postgres
├── docker-compose.ollama.yml          Ollama container override
├── Dockerfile                         Multi-stage Alpine build
├── start.sh                           Launch script (local vs Docker Ollama)
├── pyproject.toml                     Dependencies and metadata
└── .env.example                       Environment variable template
```

---

## Quick Start

### Prerequisites

- Python ≥ 3.12
- Docker & Docker Compose
- Ollama (local) or Docker (for containerized Ollama)
- Tavily API key (free at tavily.com)

### 1. Clone and configure

```bash
git clone https://github.com/jcarlosvelasco/finance-agent
cd finance-agent
cp .env.example .env
# Edit .env with your TAVILY_API_KEY and Langfuse credentials
```

### 2. Pull the LLM model

```bash
ollama pull gemma4:e2b-mlx
```

### 3. Start services

**Option A — Local Ollama (recommended for Apple Silicon):**
```bash
ollama serve   # in a separate terminal
# Edit .env: OLLAMA_MODE=local
source .env && ./start.sh
```

**Option B — Ollama in Docker:**
```bash
# Edit .env: OLLAMA_MODE=docker
source .env && ./start.sh
```

### 4. Generate a report

```bash
curl "http://localhost:8000/generate_report?ticker=AAPL"
```

Interactive API docs: http://localhost:8000/docs

---

## Report Sections

The generated report covers seven areas:

| Section | Content |
|---|---|
| Executive Summary | One-paragraph overview of the investment thesis |
| Company Overview | Sector, industry, business description |
| Financial Health | Margins, D/E, ROE, cash position, free cash flow |
| Valuation | PE ratio, market cap, EPS, 52-week range |
| Sentiment Analysis | News sentiment classification + key events |
| Investment Perspective | Bullish/bearish factors synthesis |
| Key Takeaways | Actionable summary |

---

## Observability

All pipeline steps are traced in Langfuse with visibility into each node: validation latency, fundamentals retrieval, news search, LLM sentiment parsing, report generation, and token usage.

To access the Langfuse dashboard: http://localhost:3000

Configure credentials in `.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

---

## Development

### Mock mode (no GPU needed)

```bash
LLM_PROVIDER=mock uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Uses `GenericFakeChatModel` to return canned responses — useful for testing the pipeline without Ollama.

### Caching

Reports are cached at `src/data/reports/{TICKER}.json`. The cache expires automatically after one day (checked by file modification date). Delete a file to force regeneration on the next request.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OLLAMA_MODE` | `local` or `docker` | `local` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://host.docker.internal:11434` |
| `LLM_PROVIDER` | `ollama` or `mock` | `ollama` |
| `TAVILY_API_KEY` | Tavily search API key | — |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | — |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | — |
| `LANGFUSE_DB_PASSWORD` | Postgres password for Langfuse | `langfuse` |

See `.env.example` for the full list.

---


## License

Check [LICENSE.md](LICENSE.md)
