# 📋 Product Requirements Document (PRD)
## Project: Emergency Lang Kit (ELK)

> **Document Status:** DRAFT 2.0 (Full Vision)
> **Target Audience:** Technical Directors, Civil Protection Stakeholders
> **Vision:** "To provide an Open Source Factory that enables any community to build its own Intelligent Emergency Response System."

---

## 1. 🚨 Problem Statement

**The "Black Box" Problem:**
Current Emergency Response Systems (CAD) rely 100% on the human operator's ability to understand, translate, and type rapidly.
*   **Language Barrier:** In regions like Béjaïa (Algeria) or Gatineau (Canada), calls mix languages (Codeswitching). Standard tools fail.
*   **Scalability Block:** Building a custom AI for every dialect is too expensive ($$$).
*   **Data Loss:** ~80% of operational intelligence is lost once the call ends.

## 2. 🎯 Product Vision & Value Prop
**"The WordPress of Emergency AI — A Modular, Extensible Platform for Certified Intelligence Components."**
ELK is not a single product. It is a **Factory Platform**.
We don't just fish; we give communities the rod.

### Key Differentiators (The "Enterprise" Angle)
1.  **Vertical Scalability (Domain Packs):** A "Plug & Play" architecture to deploy the system in any vertical (Fire, Police, Medical) in any language.
2.  **The Community Factory:** A suite of No-Code tools (`scaffold`, `annotate`, `extract`) allowing non-engineers to build these packs.
3.  **Operational Memory (Analytics):** Built-in Data Warehousing for Spatio-Temporal analysis.

---

## 3. 🏗️ Functional Requirements (The Core Engine)

### 3.1 The Kinetic Engine (Ingestion & Extraction)
*   **FR-01 Multi-Lingual Ingestion (Whisper + QLoRA):**
    *   Must use `Whisper` as the base model.
    *   Must support **QLoRA Adapters** (`adapters/kabyle.bin`) for efficient low-resource fine-tuning.
    *   *Constraint:* Adapters must be hot-swappable (Standard FR -> Dialect DZ).
*   **FR-02 Context-Aware Extraction (RAG):**
    *   Must query a local Vector DB (Chroma/FAISS) *before* LLM inference.
    *   *Data:* Must index specific "Knowledge Packs" (e.g., PDF Manuals, GeoJSON layers).
*   **FR-03 Strict Deterministic Output (JSON Schema):**
    *   **NO Markdown/Text:** The LLM must output *pure JSON* validated against `core/interfaces.py`.
    *   **Structure:** Must strictly adhere to ensuring `incident_type` is an Enum, not a string.

### 3.2 The Dynamic Engine (Logic & Validation)
*   **FR-04 Evaluation & Calculator Logic:**
    *   Must implement a "Confidence Calculator" (weighted average of ASR confidence + Entity presence).
    *   Must include a "Validator" module that runs business logic checks (e.g., "Is victim count possible?").
*   **FR-05 Human-in-the-Loop (Validator UI):**
    *   If `confidence < threshold`, trigger "Operator Alert".
    *   UI must show specific "Reasoning Trace" (Why did the AI choose 'Fire'?).

### 3.3 Infrastructure & Deployment
*   **FR-06 Cloud / Local Toggle:**
    *   **Hybrid Mode:** Switch between Cloud LLM (GPT-4 via API) and Local LLM (Llama 3 via Ollama) with a simple config flag `use_local_llm=True`.
    *   *Rationale:* Critical for data privacy (Local) vs performance (Cloud).
    *   **Air-Gapped Capable:** Must run without internet if required.

### 3.4 The "Community Factory" (Contributor Tools)
*   **FR-09 Scout Tool (Annotation):** A lightweight Streamlit UI for contributors to listen to audio, correct transcripts, and validate entity extraction.
*   **FR-10 Knowledge Refinery (Extraction):** A workflow to ingest raw PDFs (e.g., Procedure Manuals), extract candidate Enums/Rules via LLM, and present them for human validation.
*   **FR-11 Rule Builder (No-Code):** A simple YAML-based syntax or UI to define dispatch logic (`If FIRE then TRUCK`) without writing Python code.
    *   *Constraint:* All rules are **validated, versioned, and simulated** before activation.
*   **FR-12 Pack Packager:** A CLI command `elk package` that bundles the Lexicon, Rules, and Models into a shareable `.zip`.

### 3.4 The Analytics Layer (Business Intelligence)
*   **FR-06 Data Warehousing:** Log every call in structured JSONL format (`timestamp`, `lat/lon`, `incident`, `action`).
*   **FR-07 Spatio-Temporal Analysis:** Enable Heatmap generation (Incident Density by Time/Location).

---

## 4. 🗺️ Success Metrics (KPIs)
*   **Technical:** 98% Schema Validation Pass Rate.
*   **Community:** Time to create a new "Language Pack" < 1 week.
*   **Operational:**
    *   Reduce "Time to Dispatch" by 30% for dialect speakers.
    *   **Human Override Rate < 15%** after 3 months (Demonstrates AI/Human Trust).
