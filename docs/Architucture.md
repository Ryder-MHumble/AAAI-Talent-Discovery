# AAAI-26 Talent Hunter - System Architecture

## 系统架构图 (System Architecture)

```mermaid
graph TB
    subgraph "External Systems"
        A[BD/HR System]
        B[AAAI-26 Website]
    end
    
    subgraph "FastAPI Service Layer"
        C[API Endpoints]
        C1[POST /check-person]
        C2[POST /jobs/aaai-full-scan]
        C3[GET /jobs/export]
        
        C --> C1
        C --> C2
        C --> C3
    end
    
    subgraph "LangGraph Agent Workflow"
        D[Ingestion Node]
        E[Filter Node]
        F[Detective Node]
        G[Auditor Node]
        H[Router]
        
        D -->|Load Candidates| E
        E -->|Filter Chinese Overseas| F
        F -->|Search Homepage| G
        G -->|Verify & Extract| H
        H -->|More to Process?| F
        H -->|Complete| I[Job Store]
    end
    
    subgraph "Agent Tools"
        J[Search Tool<br/>DuckDuckGo]
        K[Verify Tool<br/>HTTP + Semantic]
        L[LLM Extraction<br/>SiliconFlow]
    end
    
    subgraph "Data Layer"
        I[In-Memory Job Store]
        M[Excel Export Service]
    end
    
    A -->|API Request| C1
    A -->|API Request| C2
    C1 --> F
    C2 --> D
    B -->|Scrape| D
    
    F --> J
    G --> K
    G --> L
    
    C3 --> M
    I --> M
    
    style D fill:#e1f5ff
    style E fill:#fff9e1
    style F fill:#ffe1f5
    style G fill:#e1ffe1
```

## Agent Workflow Diagram (代理工作流)

```mermaid
stateDiagram-v2
    [*] --> Ingestion
    
    Ingestion --> Filter: Load all candidates
    
    Filter --> Detective: Mark SKIPPED<br/>(non-Chinese or mainland)
    
    Detective --> Auditor: Find homepage URL
    Detective --> Failed: No URL found
    
    Auditor --> ConnectivityCheck: Verify URL
    
    ConnectivityCheck --> SemanticMatch: HTTP 200 OK
    ConnectivityCheck --> Failed: Connection failed
    
    SemanticMatch --> LLMExtraction: Name + Affiliation match
    SemanticMatch --> Failed: Content mismatch
    
    LLMExtraction --> Verified: Extract email, CN name, bachelor
    
    Verified --> Router: Mark VERIFIED
    Failed --> Router: Mark FAILED
    
    Router --> Detective: More PENDING?
    Router --> [*]: All processed
```

## Data Flow (数据流)

```mermaid
sequenceDiagram
    participant Client as BD/HR System
    participant API as FastAPI
    participant Graph as LangGraph
    participant Tools as Agent Tools
    participant LLM as SiliconFlow LLM
    participant Store as Job Store
    
    Client->>API: POST /jobs/aaai-full-scan
    API->>Graph: Start workflow
    
    Graph->>Graph: Ingestion (Load candidates)
    Graph->>Graph: Filter (Chinese + Overseas)
    
    loop For each candidate
        Graph->>Tools: Search homepage
        Tools-->>Graph: Return URLs
        
        Graph->>Tools: Check connectivity
        Tools-->>Graph: HTTP 200
        
        Graph->>Tools: Fetch page text
        Tools-->>Graph: Page content
        
        Graph->>Graph: Semantic match
        
        Graph->>LLM: Extract profile
        LLM-->>Graph: {email, name_cn, bachelor}
        
        Graph->>Store: Update candidate status
    end
    
    Graph-->>API: Workflow complete
    API-->>Client: job_id
    
    Client->>API: GET /jobs/{id}/export
    API->>Store: Fetch results
    Store-->>API: Candidates list
    API->>API: Generate Excel
    API-->>Client: Download .xlsx
```

## Component Architecture (组件架构)

```mermaid
graph LR
    subgraph "Core Layer"
        A1[config.py<br/>Environment Settings]
        A2[llm.py<br/>SiliconFlow Client]
    end
    
    subgraph "Agent Layer"
        B1[state.py<br/>AgentState]
        B2[graph.py<br/>Workflow Definition]
        B3[nodes/<br/>Processing Nodes]
        B4[tools/<br/>Search & Verify]
    end
    
    subgraph "API Layer"
        C1[endpoints.py<br/>REST Routes]
        C2[models.py<br/>Pydantic Schemas]
    end
    
    subgraph "Service Layer"
        D1[excel_service.py<br/>Report Generation]
    end
    
    A1 --> A2
    A2 --> B2
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    C1 --> B2
    C2 --> C1
    
    B2 --> D1
    C1 --> D1
```

## Technology Stack (技术栈)

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API Framework** | FastAPI | Async REST API |
| **Agent Orchestration** | LangGraph + LangChain | Multi-agent workflow |
| **LLM Provider** | SiliconFlow (DeepSeek-V3) | Profile extraction |
| **Search Engine** | DuckDuckGo Search | Homepage discovery |
| **Web Scraping** | httpx + BeautifulSoup4 | Content extraction |
| **Chinese NLP** | xpinyin | Name validation |
| **Data Export** | pandas + openpyxl | Excel generation |
| **Configuration** | Pydantic Settings | Environment management |

## Binary Verification Logic (二元验证逻辑)

```
Input: Candidate with potential homepage URL

Step 1: Connectivity Check
├─ Send HTTP GET request
├─ Follow redirects (max 5)
└─ Result: HTTP 200? 
    ├─ Yes → Continue to Step 2
    └─ No → Mark as FAILED

Step 2: Content Extraction
├─ Parse HTML with BeautifulSoup
├─ Remove <script>, <style> tags
├─ Extract plain text
└─ Limit to 10,000 characters

Step 3: Semantic Matching
├─ Check: Name in page text? (Required)
├─ Check: Affiliation in page text? (Preferred)
└─ Check: Affiliation keywords? (Alternative)
    ├─ All checks pass → Mark as VERIFIED, Continue to Step 4
    └─ Any check fails → Mark as FAILED

Step 4: LLM Extraction (Only if VERIFIED)
├─ Send page text + context to SiliconFlow
├─ Prompt: Extract email, Chinese name, bachelor university
├─ Parse JSON response
└─ Update candidate profile
```

## Deployment Architecture (部署架构)

### Development (DEV Mode)
```
┌─────────────────────────┐
│   Developer Machine     │
│                         │
│  ┌──────────────────┐  │
│  │  FastAPI Server  │  │
│  │  localhost:8000  │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Mock Data (5)   │  │
│  └──────────────────┘  │
└─────────────────────────┘
```

### Production (PROD Mode)
```
┌──────────────────────────────────────┐
│         Cloud Server (AWS/Azure)     │
│                                      │
│  ┌────────────────────────────────┐ │
│  │      Nginx (Reverse Proxy)     │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│  ┌────────────▼───────────────────┐ │
│  │    Uvicorn (FastAPI Workers)   │ │
│  │    Multi-process mode          │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│  ┌────────────▼───────────────────┐ │
│  │   Redis/PostgreSQL (Jobs)      │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
         │                    │
         ▼                    ▼
   ┌──────────┐         ┌──────────┐
   │ AAAI.org │         │SiliconFlow│
   └──────────┘         └──────────┘
```

## API Design Principles (API 设计原则)

1. **Service-Oriented Architecture (SOA)**
   - RESTful endpoints for external integration
   - Clear separation of concerns
   - Stateless request handling

2. **Async/Await for Concurrency**
   - Non-blocking I/O for HTTP requests
   - Concurrent search operations (with rate limiting)
   - Background job processing

3. **Binary Verification**
   - Strict verification: VERIFIED or FAILED (no "maybe")
   - Multiple validation layers (connectivity → semantic → LLM)
   - Clear failure reasons for debugging

4. **Extensibility**
   - Easy to add new agent nodes
   - Pluggable search providers (DuckDuckGo → SerpAPI)
   - Configurable LLM providers

## Security Considerations (安全考虑)

- **API Key Management**: Environment variables only, never in code
- **Rate Limiting**: Control concurrent searches to avoid IP bans
- **Input Validation**: Pydantic models for all API inputs
- **Error Handling**: Graceful degradation, no sensitive info in errors
- **CORS**: Configurable allowed origins for production

## Performance Optimization (性能优化)

- **Concurrent Searches**: Process multiple candidates in parallel (configurable)
- **Early Exit**: Stop processing if verification fails early
- **Text Truncation**: Limit page text to 10K chars to reduce LLM costs
- **Caching**: (Future) Cache search results for common affiliations

## Future Enhancements (未来增强)

1. **Database Integration**: Replace in-memory store with PostgreSQL/Redis
2. **Advanced Search**: Add SerpAPI for better results
3. **Firecrawl Integration**: Deep content extraction
4. **Webhook Notifications**: Alert when jobs complete
5. **Rate Limiting**: Add per-IP rate limits
6. **Monitoring**: Add Prometheus metrics
7. **Admin Dashboard**: Web UI for job management