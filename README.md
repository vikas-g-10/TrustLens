# TrustLens — AI Digital Evidence Investigator

**Verify before you believe. Investigate before you share.**

TrustLens is an AI-assisted digital evidence investigation prototype designed to help people examine online claims, evaluate sources, compare conflicting evidence, and explore potential signs of manipulated or synthetic media.

As AI-generated videos, synthetic voices, misleading clips, and edited media become easier to create, it is increasingly difficult to distinguish authentic evidence from content that needs closer inspection. TrustLens explores how multiple evidence signals, explainable reasoning, and visual investigation tools can help people make more informed decisions.

🌐 **Live Demo:** https://trust-lens-kappa-henna.vercel.app/

💻 **Source Code:** [GitHub Repository](https://github.com/vikas-g-10/TrustLens)

---

## Table of Contents

* [The Problem](#-the-problem)
* [What Is TrustLens?](#-what-is-trustlens)
* [Features](#-features)
* [Real-World Impact: Shorts Analyzer](#-real-world-impact-shorts-analyzer)
* [From Web Prototype to Browser Extension](#-future-scope-browser-extension)
* [How to Try the Live Demo](#-how-to-try-the-live-demo)
* [Download and Run Locally](#-download-and-run-locally)
* [Technology Stack](#-technology-stack)
* [Limitations and Responsible Use](#️-limitations-and-responsible-use)
* [Future Improvements](#-future-improvements)

---

## 🔎 The Problem

Digital content can influence public opinion, purchasing decisions, reputations, and trust in information. A short video, a convincing synthetic voice, or a manipulated image can circulate widely before its origin or context is properly examined.

Common challenges include:

* **Synthetic media:** AI-generated videos, voices, and images can appear convincing.
* **Missing context:** Genuine footage can be misleading when edited, cropped, or shared without its original context.
* **Conflicting information:** Different sources may present contradictory claims.
* **Unclear explanations:** A simple “real” or “fake” label doesn't explain the evidence behind a decision.
* **Friction during verification:** People often have to switch between multiple websites and tools to investigate suspicious content.

TrustLens explores a more transparent approach: bring investigation tools and evidence signals into one workspace so users can examine a claim rather than blindly trusting a verdict.

## 🛡️ What Is TrustLens?

TrustLens is a web-based prototype for AI-assisted digital forensics and evidence investigation.

It combines an interactive interface with a backend analysis pipeline to explore claims, source reliability, URL-related signals, conflicting evidence, and short-form video inspection.

The goal is not to replace human judgement with an unquestionable AI verdict. It is to help users understand what has been examined, what signals may matter, and where additional verification is needed.

## ✨ Features

### 1. Investigation Workspace

Start an investigation using the available input workflow and examine the information returned by the analysis pipeline.

The goal is to turn an initial question or suspicious item into a more structured investigation.

### 2. Evidence Battle

Compare competing claims or evidence and explore where information agrees or conflicts.

This helps illustrate why verification should consider multiple signals rather than rely on a single statement or source.

### 3. Evidence Graph

Explore relationships between pieces of evidence and their associated sources through a visual investigation interface.

A graph-based approach can help users understand how information is connected and identify areas that deserve closer inspection.

### 4. Explainable Verdicts — “Why This Verdict?”

TrustLens includes an interface for presenting the reasoning behind an assessment.

Instead of treating a result as a black box, the experience emphasizes understanding the signals and explanations associated with it. The strength of any conclusion depends on the quality and availability of the underlying evidence.

### 5. Evidence Timeline

Review investigation events and evidence in a timeline-oriented view.

This can help organize information and make the sequence of findings easier to follow.

### 6. Shorts Analyzer

The Shorts Analyzer is a demonstration of how short-form video evidence could be inspected through an accessible verification interface.

It presents a vertical video player, audit status, confidence information, and an analysis workflow for exploring the media being examined.

See the dedicated section below for the intended real-world use case and future browser-extension concept.

---

## 🎬 Real-World Impact: Shorts Analyzer

Short-form videos are easy to watch and share, but their original source, context, editing history, or use of synthetic media may not be immediately obvious.

The TrustLens Shorts Analyzer demonstrates a possible first step toward making media verification more accessible.

### Screenshot

![TrustLens Shorts Analyzer showing the video player and forensic audit interface](docs/images/shorts-analyzer.png)

*TrustLens Shorts Analyzer prototype. The displayed demo includes a clip labelled “Synthetic celebrity speech” and states that no real person is depicted.*

### What the demo demonstrates

* **Video-first inspection:** Examine a short-form clip in a familiar vertical-video interface.
* **Visible audit status:** Display an assessment label alongside the clip.
* **Confidence information:** Show a confidence indicator as part of the demonstration interface.
* **Accessible workflow:** Explore the idea of bringing media inspection closer to where people consume videos.
* **A foundation for contextual verification:** Illustrate how a viewer might be encouraged to investigate a clip before sharing or relying on it.

The labels and scores shown in the interface are outputs of the current prototype and should not be interpreted as independent proof that a video is authentic, manipulated, or AI-generated.

### Why this matters in the real world

Imagine a user comes across a short clip containing a public claim, an apparently familiar voice, or footage that seems suspicious.

A future version of TrustLens could help the user:

1. Inspect the clip without leaving the page where it appears.
2. Review available source and context information.
3. Examine potential indicators of synthetic generation or editing.
4. See the reasoning and limitations associated with the analysis.
5. Decide whether further verification is needed before sharing the clip.

This could be useful in media literacy, journalism, education, online safety, and everyday information checking.

**Important:** These are intended use cases, not a claim that the current demo reliably detects every deepfake or independently verifies every video.

## 🧩 Future Scope: Browser Extension

The current Shorts Analyzer is a **web prototype**, not a published browser extension. A future implementation could bring the same concept directly into a user's browsing experience.

A possible extension workflow would be:

1. **Browse:** A user encounters a short video on a supported website.
2. **Select:** The user opens TrustLens from the browser toolbar or a supported context menu.
3. **Analyze:** The extension sends permitted video content, a URL, or available metadata to the TrustLens analysis backend.
4. **Review:** TrustLens displays available evidence, potential manipulation indicators, confidence information, and explanations.
5. **Decide:** The user chooses whether to trust, investigate further, or share the content.

### Potential extension features

* One-click analysis from supported video pages.
* A side panel showing the investigation results.
* Source and context checks where data is available.
* Explainable findings instead of unexplained real/fake labels.
* Links to supporting evidence and a record of previous checks.
* Clear warnings when the analysis is inconclusive or the source cannot be accessed.

### What would be needed?

A production extension would require browser-specific integration, permissions and privacy controls, reliable video or metadata extraction, secure backend communication, error handling, and testing across supported websites.

Access restrictions, encrypted streams, DRM, platform policies, and unavailable source information may prevent some videos from being analyzed. The extension should explain these limitations rather than invent results.

This extension is a **future development direction**; it is not currently included as an installable product in this repository.

---

## 🚀 How to Try the Live Demo

You can explore the deployed application without installing the source code.

1. Open the [TrustLens Live Demo](https://trust-lens-kappa-henna.vercel.app/).
2. Use the navigation to explore **Investigation**, **Evidence Battle**, **Evidence Graph**, **Why This Verdict**, and **Timeline**.
3. Open **Shorts Analyzer** to see the video-based audit interface.
4. Explore the available demo clips and controls.
5. If you submit your own material, follow the available upload and analysis workflow.

Some features may depend on the backend service, third-party API availability, and the type of content submitted. The demo should be treated as an experimental prototype rather than a production-grade verification service.

---

## 💻 Download and Run Locally

To explore the implementation or develop your own improvements, download the repository and run the frontend and backend locally.

### Prerequisites

* Git
* Node.js 18 or newer
* Python 3.10 or newer
* A Groq API key for AI-backed functionality, where required

### Option 1: Download as a ZIP

1. Open the [TrustLens GitHub repository](https://github.com/vikas-g-10/TrustLens).
2. Click **Code → Download ZIP**.
3. Extract the ZIP file to a folder on your computer.
4. Open a terminal in the extracted project directory.
5. Follow the installation steps below.

### Option 2: Clone with Git

```bash
git clone https://github.com/vikas-g-10/TrustLens.git
cd TrustLens
```

### Step 1: Install backend dependencies

From the repository root:

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

### Step 2: Install frontend dependencies

From the repository root:

```bash
npm install
```

### Step 3: Configure environment variables

Create a `.env` file in the location expected by the backend configuration. For the current project setup, the backend reads `.env` and `.env.local` from its working directory.

Example configuration:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
SEARCH_PROVIDER=duckduckgo
```

Replace the placeholder with your own API key. Configure optional integrations only if needed by the features you want to run.

**Security:** Never commit your `.env` file, publish API keys, or embed private API credentials in frontend code.

### Step 4: Start TrustLens

The repository provides a development runner:

```bash
python run_dev.py
```

Alternatively, use the configured npm development script:

```bash
npm run dev
```

If you prefer to run the services separately, open two terminals and use the scripts defined in `package.json`:

```bash
npm run dev:fastapi
```

```bash
npm run dev:vite
```

### Step 5: Open the application

The project's documented local addresses are:

* **Frontend:** http://localhost:3000
* **FastAPI documentation:** http://localhost:8000/docs

The Vite development configuration proxies `/api/*` requests to the local FastAPI backend.

If a command fails, check the installed dependencies, environment configuration, and the scripts available in the repository's `package.json`.

---

## 🏗️ Technology Stack

| Component            | Technology                |
| -------------------- | ------------------------- |
| Frontend             | React, Vite, Tailwind CSS |
| Backend              | Python, FastAPI           |
| AI integration       | Groq API, when configured |
| Search and retrieval | DuckDuckGo integration    |
| API documentation    | FastAPI / Swagger UI      |
| Deployment           | Vercel                    |

The frontend provides the interactive investigation experience, while the backend exposes API endpoints for supported analysis workflows.

---

## ⚠️ Limitations and Responsible Use

TrustLens is a prototype intended to demonstrate an approach to digital evidence investigation. It should not be treated as a definitive authority on authenticity or truth.

### Groq API rate limits

AI-powered features may use the Groq API. Requests can occasionally fail or become temporarily unavailable when the configured API key reaches its rate limit or usage quota.

If an analysis fails:

1. Wait briefly and try again.
2. Check whether the backend is available.
3. Verify that the API key is configured correctly.
4. Check the applicable Groq usage limits.

A failed request does not, by itself, mean that the submitted content is authentic or suspicious.

### Other limitations

* Analysis quality depends on the available content, evidence, sources, and model outputs.
* Some websites restrict automated access or require authentication.
* Synthetic-media indicators are not conclusive proof of manipulation.
* Confidence scores are estimates, not guarantees of correctness.
* The current Shorts Analyzer is a demonstration, not a validated forensic certification system.
* Results should be reviewed critically, especially when they could affect a person's reputation, safety, or livelihood.

Use TrustLens as an investigative aid, and seek independent evidence before making consequential decisions.

---

## 🛣️ Future Improvements

Potential areas for future development include:

* A browser extension for supported short-video platforms.
* Improved source attribution and provenance reporting.
* More transparent evidence references and analysis explanations.
* Better handling of inconclusive results and service failures.
* Expanded testing across media types and real-world scenarios.
* Privacy-conscious analysis, retention controls, and secure deployment practices.
* User feedback and evaluation to measure the reliability of findings.

These are possible future improvements, not a promise that every feature is already implemented.

---

## 🧪 Verification and Testing

The repository includes test scripts for selected backend and frontend workflows. From the project root, run the relevant commands:

```bash
python backend/test_phase1.py
python backend/test_phase2.py
python backend/test_phase3.py
npm run lint
npm run build
```

These checks cover selected functionality; passing them does not establish that every media-analysis result is accurate or that every deployment integration is working.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository.
2. Create a branch for your change.
3. Make and test your changes.
4. Open a pull request describing the improvement.

Please avoid including API keys, private data, or sensitive media in commits and issue reports.

---

## 📌 Project Status

TrustLens is an experimental web application demonstrating AI-assisted evidence investigation. The live demo showcases the current interface and selected workflows, including the Shorts Analyzer.

The browser-extension experience described above is a proposed future direction, not an available installation.

**Live Demo:** https://trust-lens-kappa-henna.vercel.app/

**Repository:** https://github.com/vikas-g-10/TrustLens
