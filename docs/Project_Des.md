# Project: AAAI-26 Talent Hunter (Service-Oriented Multi-Agent System)

## 1. Project Overview
**Goal**: Build a production-ready Multi-Agent system to identify and verify "Overseas Chinese Scholars" for AAAI-26.
**Architecture**: Service-Oriented Architecture (SOA). The system exposes RESTful APIs to trigger scraping jobs or analyze specific individuals on-demand.
**Core Logic**: **Binary Verification**. The agents strictly enforce a "Verified" or "Unverified" status based on HTTP connectivity and semantic content matching.
**Target Audience**: Internal BD/HR systems.

## 2. Technology Stack
*   **Framework**: `FastAPI` (Async/Await for high-concurrency).
*   **Agent Orchestration**: `LangGraph` + `LangChain`.
*   **LLM Provider**: **SiliconFlow** (DeepSeek-V3 / Qwen2.5) via `langchain_openai`.
*   **Search Tools**: `duckduckgo-search` (Free Tier) or `serpapi` (Pro Tier).
*   **Scraping**: `httpx` + `beautifulsoup4` (Lightweight) / `firecrawl` (Optional).
*   **Data Persistence**: In-memory (for MVP) or SQLite.
*   **Export**: `pandas` + `openpyxl`.

## 3. Directory Structure
Please generate the project with this exact structure:

```text
aaai-talent-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   ├── endpoints.py     # Routes: /start-job, /check-person, /download
│   │   └── models.py        # Pydantic schemas for API Req/Res
│   ├── core/
│   │   ├── config.py        # Env vars (SILICONFLOW_API_KEY)
│   │   └── llm.py           # LLM Client initialization
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py         # LangGraph State definitions
│   │   ├── graph.py         # The Main Graph (Workflow definition)
│   │   ├── nodes/
│   │   │   ├── ingestion.py # Parsing AAAI URLs
│   │   │   ├── filter.py    # Name/Geo Filtering
│   │   │   ├── detective.py # Search & Scraping
│   │   │   └── auditor.py   # Binary Verification Logic
│   │   └── tools/
│   │   │   ├── search.py    # Search Tool wrapper
│   │   │   └── verify.py    # HTTP & Content checking tool
│   └── services/
│       └── excel_service.py # Generates .xlsx files
├── .env.example
├── requirements.txt
└── README.md
```

## 4. Agent Workflow Design (LangGraph)

The system should run a **StateGraph** with the following nodes:

### Shared State (`AgentState`)
```python
class AgentState(TypedDict):
    job_id: str
    candidates: List[CandidateProfile] # The main list
    current_index: int                 # Processing pointer
    is_complete: bool
```

### Node 1: `IngestionNode`
*   **Trigger**: API Call to `/start-job`.
*   **Function**: Fetches the fixed AAAI-26 URLs (Invited Speakers, Technical Track).
*   **Output**: Populates `candidates` list with raw data (Name, Affiliation, Role).

### Node 2: `FilterNode`
*   **Function**: Iterates through `candidates`.
*   **Logic**:
    1.  **Pinyin Check**: Uses `xpinyin` to validate if the name looks Chinese.
    2.  **Geo Check**: Checks if Affiliation contains "China", "Tsinghua", etc.
*   **Action**: Marks non-targets as `status="SKIPPED"`.

### Node 3: `DetectiveNode` (The Worker)
*   **Function**: Processes one `PENDING` candidate at a time.
*   **Tools**:
    *   `search_tool`: Searches `"{Name}" "{Affiliation}" homepage`.
    *   `scrape_tool`: Fetches page text.
*   **Action**: Finds a potential URL and passes it to the Auditor.

### Node 4: `AuditorNode` (The Gatekeeper)
*   **Function**: Performs **Binary Verification**.
*   **Logic**:
    1.  **Connectivity**: Is HTTP Status 200?
    2.  **Semantic Match**: Does page text contain `Name` AND (`Affiliation` OR `Paper Keywords`)?
*   **LLM Extraction**: If Verified, uses SiliconFlow LLM to extract:
    *   `email`
    *   `name_cn`
    *   `bachelor_univ` (Look for "BS", "Bachelor")
*   **Output**: Updates candidate status to `VERIFIED` or `FAILED`.

## 5. API Interface Design (`endpoints.py`)

### Endpoint 1: **On-Demand Check (Fast)**
*   `POST /api/v1/check-person`
*   **Input**: `{"name": "Haoyang Li", "affiliation": "CMU"}`
*   **Behavior**: Spawns a mini-graph to check just this one person.
*   **Output**: `{"status": "VERIFIED", "homepage": "...", "bachelor": "SJTU"}`
*   **Use Case**: External system wants to check a specific scholar immediately.

### Endpoint 2: **Batch Job Trigger**
*   `POST /api/v1/jobs/aaai-full-scan`
*   **Input**: `{"limit": 10}` (Optional limit for testing)
*   **Behavior**: Starts background scraping of AAAI URLs.
*   **Output**: `{"job_id": "12345", "msg": "Job started"}`

### Endpoint 3: **Export Results**
*   `GET /api/v1/jobs/{job_id}/export`
*   **Output**: Returns an `.xlsx` file matching the business requirement columns.

## 6. Implementation Specifications for Cursor

1.  **SiliconFlow Configuration**:
    *   In `core/llm.py`, initialize `ChatOpenAI`:
        ```python
        ChatOpenAI(
            base_url="https://api.siliconflow.cn/v1",
            api_key=settings.SILICONFLOW_API_KEY,
            model="deepseek-ai/DeepSeek-V3" # or Qwen/Qwen2.5-72B-Instruct
        )
        ```
2.  **Concurrency Control**:
    *   The `DetectiveNode` should perform searches sequentially or with a small semaphore (e.g., 3 concurrent requests) to avoid IP bans from search engines.
3.  **Mocking for MVP**:
    *   Since scraping the full AAAI Technical Track (600+ names) is heavy, include a **Mock Mode** in `IngestionNode` that returns 5 hardcoded real examples (e.g., "Yi Wu at Google", "Haoyang Li at CMU") when `env=DEV`.
4.  **Error Handling**:
    *   If a search fails, log it and continue. Do not break the API loop.
    *   Use `try-except` around `requests.get`.

## 7. Prompts

**Profile Extraction Prompt (System)**:
```text
You are an expert HR researcher. 
I will provide the text content of a scholar's homepage.
You must extract the following fields into JSON:
- `name_cn`: Chinese name characters (e.g., "张三"). Return null if not found.
- `email`: Email address. Return null if not found.
- `bachelor_univ`: The university where they obtained their Bachelor's/Undergraduate degree. Look for "B.S.", "B.E.", "Bachelor".
- `is_verified`: boolean. True if the page explicitly mentions the input affiliation.
```