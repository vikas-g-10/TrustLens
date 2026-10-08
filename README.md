# TrustLens — AI Digital Evidence Investigator

Desktop-first AI digital forensics platform investigating claims, provenance, URL security, source reliability, and conflicting evidence beyond simple fake-detection.

## Architecture

- **Frontend**: React + Vite + Tailwind CSS (Port 3000)
- **Backend**: Python + FastAPI AIML Architecture (Port 8000)
- **Proxy**: Vite proxies `/api/*` to `http://127.0.0.1:8000`

---

## Quick Start

### 1. Prerequisites
- **Python**: 3.10+ (tested on Python 3.14)
- **Node.js**: 18+

### 2. Setup
```bash
# Python dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
npm install
```

### 3. Environment Variables (Optional)
Create `.env` (or `.env.local`):
```ini
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="llama-3.3-70b-versatile"
SEARCH_PROVIDER="duckduckgo"
```
*(Search retrieval runs with DuckDuckGo out of the box with zero paid API keys).*

### 4. Run Locally
```bash
# Run both FastAPI backend and Vite frontend together
npm run dev
# or: python run_dev.py
```
- Open `http://localhost:3000` in your browser.
- FastAPI Swagger Documentation is available at `http://localhost:8000/docs`.

### Individual Services
```bash
# Backend only
npm run dev:fastapi

# Frontend only
npm run dev:vite
```

---

## Verification & Testing

```bash
# Phase 1: FastAPI Foundation Contract
python backend/test_phase1.py

# Phase 2: URL Inspection & SSRF Protections
python backend/test_phase2.py

# Phase 3: Search Retrieval, Reliability & Source Independence
python backend/test_phase3.py

# Frontend Lint & Build
npm run lint
npm run build
```
