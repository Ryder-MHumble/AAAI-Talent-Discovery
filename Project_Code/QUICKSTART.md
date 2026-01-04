# 🚀 Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd Project_Code
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file with your SiliconFlow API key:

```bash
# Copy the example file
cp .env.example .env

# Edit and add your API key
nano .env  # or use any text editor
```

**Required Configuration**:
```env
SILICONFLOW_API_KEY=your_api_key_here
APP_ENV=DEV
```

> 💡 Get your API key from: https://cloud.siliconflow.cn/

### Step 3: Start the Service

```bash
python app/main.py
```

Or use the quick start script (Unix/Mac):

```bash
chmod +x start.sh
./start.sh
```

The service will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs

---

## 🧪 Test the System

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "AAAI Talent Hunter",
  "version": "1.0.0"
}
```

---

### Test 2: Check a Single Person

Open http://localhost:8000/docs and try the **POST /api/v1/check-person** endpoint with:

```json
{
  "name": "Haoyang Li",
  "affiliation": "Carnegie Mellon University"
}
```

Or use curl:

```bash
curl -X POST http://localhost:8000/api/v1/check-person \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Haoyang Li",
    "affiliation": "Carnegie Mellon University"
  }'
```

---

### Test 3: Run a Batch Job

```bash
# Start a job (processes 5 mock candidates in DEV mode)
curl -X POST http://localhost:8000/api/v1/jobs/aaai-full-scan \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

**Response** (copy the `job_id`):
```json
{
  "job_id": "job-abc123def456",
  "message": "Job started successfully",
  ...
}
```

**Check Status**:
```bash
curl http://localhost:8000/api/v1/jobs/job-abc123def456/status
```

**Download Results** (when status is "COMPLETED"):
```bash
curl -O http://localhost:8000/api/v1/jobs/job-abc123def456/export
```

This downloads an Excel file with verified scholars!

---

## 📊 Understanding the Results

### Status Codes

- **VERIFIED** ✅ - Scholar successfully verified with homepage
- **FAILED** ❌ - Could not verify (no homepage, unreachable, or mismatch)
- **SKIPPED** ⏭️ - Not a target (non-Chinese name or mainland China affiliation)

### Extracted Fields

| Field | Description |
|-------|-------------|
| `name` | Full name in English |
| `name_cn` | Chinese name (if found) |
| `affiliation` | Current institution |
| `homepage` | Verified personal homepage URL |
| `email` | Email address (if found) |
| `bachelor_univ` | Undergraduate university (if found) |

---

## 🔄 Switching to Production Mode

To scrape **real AAAI-26 data** instead of mock data:

1. Edit `.env`:
```env
APP_ENV=PROD
```

2. Restart the service:
```bash
python app/main.py
```

> ⚠️ **Note**: Production mode will scrape actual AAAI-26 pages. This may take longer and is subject to rate limits.

---

## 🛠️ Troubleshooting

### Error: "SILICONFLOW_API_KEY not found"

**Solution**: Make sure you've created `.env` with a valid API key.

### Error: "ModuleNotFoundError"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Service won't start

**Solution**: Check if port 8000 is already in use:
```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Or start on a different port
uvicorn app.main:app --port 8001
```

---

## 📖 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [API Documentation](http://localhost:8000/docs) (when running)
- Check [Architecture Docs](../docs/Architucture.md) for system design

---

**Questions?** Check the logs in the terminal for detailed processing information.

