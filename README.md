# AAAI-26 Talent Hunter 🎯

> **Service-Oriented Multi-Agent System for Identifying Overseas Chinese Scholars**

A production-ready FastAPI service that uses LangGraph agents to automatically discover, verify, and profile Chinese scholars participating in AAAI-26 who are studying or working abroad.

---

## 🌟 Features

- **🤖 Multi-Agent Architecture**: LangGraph-powered workflow with specialized agents
- **🔍 Intelligent Search**: Automated homepage discovery using DuckDuckGo
- **✅ Binary Verification**: Strict HTTP connectivity + semantic content matching
- **🧠 LLM-Powered Extraction**: Uses SiliconFlow (DeepSeek-V3/Qwen2.5) for structured data extraction
- **📊 Excel Export**: Business-ready reports with verified scholars
- **🚀 RESTful API**: Service-oriented architecture for easy integration
- **⚡ Async/Await**: High-concurrency FastAPI backend

---

## 🏗️ Architecture

### Agent Workflow

```
┌─────────────┐
│  Ingestion  │ ──> Fetch AAAI-26 candidates
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Filter    │ ──> Identify Chinese names + overseas affiliations
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Detective  │ ──> Search for homepages
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Auditor   │ ──> Verify + Extract (Email, Chinese Name, Bachelor Univ)
└─────────────┘
```

### Technology Stack

- **Framework**: FastAPI (Async)
- **Agents**: LangGraph + LangChain
- **LLM**: SiliconFlow (DeepSeek-V3 / Qwen2.5-72B)
- **Search**: DuckDuckGo Search (Free Tier)
- **Scraping**: httpx + BeautifulSoup4
- **Export**: pandas + openpyxl

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and navigate
cd Project_Code

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your SiliconFlow API key:

```env
SILICONFLOW_API_KEY=your_actual_api_key_here
APP_ENV=DEV  # Use DEV for testing with mock data
```

### 3. Run the Service

```bash
# Option 1: Using Python directly
python app/main.py

# Option 2: Using Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will start at: **http://localhost:8000**

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "AAAI Talent Hunter",
  "version": "1.0.0"
}
```

---

### 2. Check Single Person (Fast)

**Use Case**: External BD/HR system wants to verify a specific scholar immediately.

```bash
POST /api/v1/check-person
Content-Type: application/json

{
  "name": "Haoyang Li",
  "affiliation": "Carnegie Mellon University"
}
```

**Response**:
```json
{
  "name": "Haoyang Li",
  "affiliation": "Carnegie Mellon University",
  "status": "VERIFIED",
  "homepage": "https://haoyangle.com",
  "email": "haoyang@cmu.edu",
  "name_cn": "李浩阳",
  "bachelor_univ": "Shanghai Jiao Tong University"
}
```

---

### 3. Start Batch Job

**Use Case**: Scrape all AAAI-26 candidates in the background.

```bash
POST /api/v1/jobs/aaai-full-scan
Content-Type: application/json

{
  "limit": 10  # Optional: limit for testing
}
```

**Response**:
```json
{
  "job_id": "job-a1b2c3d4e5f6",
  "message": "Job started successfully",
  "total_candidates": 0,
  "started_at": "2026-01-04T10:30:00"
}
```

---

### 4. Check Job Status

```bash
GET /api/v1/jobs/{job_id}/status
```

**Response**:
```json
{
  "job_id": "job-a1b2c3d4e5f6",
  "status": "RUNNING",
  "progress": 7,
  "total": 10,
  "verified_count": 3,
  "failed_count": 2,
  "skipped_count": 2
}
```

---

### 5. Export Results (Excel)

```bash
GET /api/v1/jobs/{job_id}/export?format=verified
```

**Parameters**:
- `format=verified` - Only verified scholars (default)
- `format=full` - All candidates with all statuses

**Response**: Downloads an `.xlsx` file with:
- **Sheet 1**: Verified Scholars (Name, Chinese Name, Affiliation, Email, Bachelor Univ, etc.)
- **Sheet 2**: Summary Statistics

---

## 🧪 Testing with Mock Data

The system includes 5 real mock candidates for testing in `DEV` mode:

1. **Haoyang Li** @ CMU
2. **Yi Wu** @ Google DeepMind
3. **Jie Tang** @ Tsinghua (will be SKIPPED - mainland China)
4. **Xiaojun Chang** @ University of Sydney
5. **Lei Chen** @ HKUST

### Test the Full Workflow

```bash
# 1. Start a job
curl -X POST http://localhost:8000/api/v1/jobs/aaai-full-scan \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# Copy the job_id from response

# 2. Check status
curl http://localhost:8000/api/v1/jobs/{job_id}/status

# 3. Download results (when completed)
curl -O http://localhost:8000/api/v1/jobs/{job_id}/export
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SILICONFLOW_API_KEY` | SiliconFlow API key (required) | - |
| `SILICONFLOW_MODEL` | LLM model name | `deepseek-ai/DeepSeek-V3` |
| `APP_ENV` | `DEV` (mock) or `PROD` (real scraping) | `DEV` |
| `CONCURRENT_SEARCHES` | Max concurrent search requests | `3` |
| `AAAI_INVITED_SPEAKERS_URL` | AAAI invited speakers page | Official URL |
| `AAAI_TECHNICAL_TRACK_URL` | AAAI technical track page | Official URL |

---

## 📊 Data Flow

### Binary Verification Logic

```
1. Connectivity Check
   ├─ HTTP 200? ✅ → Continue
   └─ Otherwise ❌ → FAILED

2. Semantic Match
   ├─ Name in page text? ✅
   ├─ Affiliation in page? ✅
   └─ Both present? ✅ → VERIFIED

3. LLM Extraction (if VERIFIED)
   ├─ Email address
   ├─ Chinese name (name_cn)
   └─ Bachelor's university
```

---

## 🏗️ Project Structure

```
Project_Code/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   ├── endpoints.py     # API routes
│   │   └── models.py        # Pydantic schemas
│   ├── core/
│   │   ├── config.py        # Settings management
│   │   └── llm.py           # LLM client
│   ├── agents/
│   │   ├── state.py         # Agent state definition
│   │   ├── graph.py         # LangGraph workflow
│   │   ├── nodes/           # Agent nodes
│   │   │   ├── ingestion.py
│   │   │   ├── filter.py
│   │   │   ├── detective.py
│   │   │   └── auditor.py
│   │   └── tools/           # Search & verify tools
│   │       ├── search.py
│   │       └── verify.py
│   └── services/
│       └── excel_service.py # Excel generation
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎯 Production Deployment

### Switching to Production Mode

1. Update `.env`:
```env
APP_ENV=PROD
```

2. The system will now scrape real AAAI-26 pages instead of using mock data.

### Performance Considerations

- **Concurrency**: Adjust `CONCURRENT_SEARCHES` (default: 3) to avoid rate limits
- **Timeout**: Search/scraping timeouts are set to 10-15 seconds
- **Rate Limiting**: Add FastAPI rate limiting middleware for production
- **Database**: Replace in-memory `job_store` with Redis/PostgreSQL

---

## 🐛 Troubleshooting

### Issue: "Search failed"

**Solution**: DuckDuckGo may rate-limit. Reduce `CONCURRENT_SEARCHES` or add delays.

### Issue: "LLM extraction failed"

**Solution**: 
1. Check your SiliconFlow API key
2. Verify the model name is correct
3. Check SiliconFlow API status

### Issue: "No suitable homepage found"

**Solution**: This is expected for some scholars. The agent will mark them as `FAILED` and continue.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

This is a business intelligence tool. For internal use only.

---

## 📧 Support

For issues or questions, contact the development team.

---

**Built with ❤️ using LangGraph, FastAPI, and SiliconFlow**

