# 🏗️ Architecture: ELK System Design

## Overview

Emergency Lang Kit follows a **3-layer architecture**:

```
┌──────────────────────────────────────────┐
│           APPLICATION LAYER              │
│  (Tools: Annotation, Analytics, etc.)    │
└──────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────┐
│         LANGUAGE PACK LAYER              │
│  (fr-FR, en-US, ar-DZ, etc.)             │
└──────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────┐
│            KERNEL LAYER                  │
│  (Core logic, language-agnostic)         │
└──────────────────────────────────────────┘
```

---

## Layer 1: Kernel (Core)

**Location:** `core/`
**Responsibility:** Universal emergency call processing logic.

### Components

#### 1.1 ASR Pipeline (`core/pipeline.py`)
Abstracts the Speech-to-Text engine.
*   **Input:** Raw Audio (WAV stream).
*   **Output:** Transcribed Text + Confidence.
*   **Logic:** Loads the appropriate fine-tuned Whisper adapter from the active Language Pack.

#### 1.2 Intent Extractor (`core/intent.py`)
Uses LLMs to extract structured data.
*   **Constraint:** Must output **Strict JSON** validated by `core/schemas.py`.
*   **Example schema:** `{ incident_type: Enum, urgency: Enum }`.

#### 1.3 Decision Engine (`core/dispatcher.py`)
Calculates the "Resonance" between the extracted intent and available resources.
*   **Logic:** `If Fire AND High_Urgency THEN Recommend Fire_Station_A`.
*   **Output:** `DecisionProposal` with a confidence score.

#### 1.4 Audit Logger (`core/analytics.py`)
Records every step for legal compliance.
*   **Storage:** SQLite (local) or PostgreSQL (enterprise).
*   **Format:** JSONL with timestamp, lat/lon, and "Reasoning Trace".

---

## Layer 2: Language Packs

**Location:** `packs/{lang-code}/`
**Responsibility:** Domain-specific data (No Code).

A pack is a folder containing:
1.  **Lexicon:** `enums/incident_types.json` (The words for "Fire" in local dialect).
2.  **Rules:** `rules.yaml` (Dispatch logic).
3.  **Model:** `adapters/whisper-lora.bin` (Fine-tuned weights).
4.  **Prompts:** `prompts/intent.txt` (Localized system prompts).

---

## Layer 3: Tools (Plugins)

**Location:** `tools/`

*   **Scaffold:** Generates new Pack structures.
*   **Annotate:** Web UI (Streamlit) for Human-in-the-Loop training.
*   **Train:** Wrapper around Unsloth/QLoRA for model fine-tuning.

---

## Data Flow (End-to-End)

1.  **Audio Call** (Input)
2.  **ASR Pipeline** → Transcribes using Pack Model.
3.  **Intent Extractor** → LLM extracts JSON intent.
4.  **Entity Recognizer** → Extracts Location/People.
5.  **Decision Engine** → Computes Dispatch Proposal.
6.  **Validator** → Checks Confidence (Human Loop if < 0.9).
7.  **Audit Log** → Saves Trace.
8.  **Dispatch** → API Call to CAD System.
