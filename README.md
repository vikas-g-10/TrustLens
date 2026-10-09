# TrustLens — Digital Evidence Investigation & Provenance

TrustLens is a desktop-first forensic investigative platform designed to help journalists, researchers, and investigators assess the reliability of digital media and online information. Unlike black-box "fake detection" tools, TrustLens leverages a **deterministic evidence fusion engine** to provide transparent, explainable, and justifiable assessments of digital provenance, source reliability, and media integrity.

---

## 🔬 Forensic Philosophy & Epistemic Guarantees

TrustLens is built on the belief that automated tools should assist—not replace—human investigators. We prioritize **traceability** over **scoring**:

1.  **Deterministic Fusion**: The AI does not decide the final verdict. Verdicts are derived through verifiable code-based rules, ensuring consistency.
2.  **No False Penalization**: Missing metadata is never treated as evidence of manipulation; tools explicitly account for honest document preparation and compression.
3.  **Source Independence**: Duplicate evidence and wire-syndication are discounted to prevent double-counting.
4.  **Transparent Inconclusivity**: When evidence is sparse or contradictory, the system explicitly defaults to `INCONCLUSIVE` rather than forcing a low-confidence decision.

---

## 🚀 Key Capabilities

### 1. Evidence Fusion (Phase 6)
Analyzes multiple normalized inputs—provenance logs, search findings, and metadata—synthesizing them into a single, explainable "Trust Triangle" of evidentiary strength.

### 2. Video Analysis (Phase 8)
Orchestrates complex video investigation by:
- Probing video containers and codecs.
- Sampling representative frames.
- Reusing the trusted image analysis pipeline (ELA, OCR, CV) for per-frame validation.
- Aggregating frame-based findings without duplicating forensic core logic.

### 3. URL & Provenance Security
Inspects links for SSRF vulnerabilities and evaluates the reputation/independence of source entities to build a robust evidence chain.

---

## 🏗️ Architecture Deep Dive

### System Layout
- **Frontend**: A React+Vite dashboard with Tailwind CSS, providing granular, componentized forensic output.
- **Backend**: FastAPI-powered engine.
    - `services/fusion/`: Deterministic synthesis engine.
    - `services/video_analysis/`: Video decoding, frame-sampling, and orchestration.
    - `services/image_analysis/`: Core computer vision and metadata verification routines.

### Data Flow
1. **Ingestion**: Upload a file (Video/Image) or submit a URL.
2. **Analysis**: Independent services (URL, Image, Video) generate `NormalizedEvidenceItem` objects.
3. **Fusion**: `FusionEngine` aggregates directed strength across hypotheses (e.g., "AUTHENTIC" vs "AI_GENERATED") to arrive at a final verdict.

---

## 🛠️ Quick Start

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

### 3. Environment Variables
Create `.env` (or `.env.local`):
```ini
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="llama-3.3-70b-versatile"
SEARCH_PROVIDER="duckduckgo"
```

### 4. Running the Platform
```bash
# Run both FastAPI backend and Vite frontend
npm run dev
```

---

## 🧪 Testing & Verification

TrustLens relies on a modular, phase-based testing suite to maintain forensic integrity for each new detection capability.

| Phase | Component | Focus |
| :--- | :--- | :--- |
| **Phase 1** | Foundation | API/FastAPI Contracts |
| **Phase 2** | URL/Web | Inspection & SSRF Protections |
| **Phase 3** | Retrieval | Search Independence |
| **Phase 6** | **Fusion** | Deterministic verdict synthesis |
| **Phase 8** | **Video** | Orchestration & frame sampling |

**Run all forensics tests:**
```bash
python backend/test_phase1.py
python backend/test_phase2.py
python backend/test_phase3.py
python backend/test_phase6.py
python backend/test_phase8.py