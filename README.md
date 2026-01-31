# 🚨 Emergency Lang Kit (ELK)

> **Production-ready framework for building intelligent emergency call systems in any language.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](docs/)
[![Status](https://img.shields.io/badge/status-implementation%20phase-green.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

---

## 🌍 The Problem

Emergency services worldwide face critical challenges:
- **Language barriers** (immigrants, tourists, multilingual regions).
- **Inconsistent call handling** (human error, stress, fatigue).
- **No structured traceability** (legal issues, quality assurance).
- **Impossible to scale** (custom solutions per region).

**Emergency Lang Kit (ELK)** solves this through a modular, language-agnostic architecture.

---

## ✨ Key Innovation

Unlike monolithic emergency systems, ELK is built on a **Kernel + Plugins** architecture:

```mermaid
graph TD
    Kernel[⚙️ ELK KERNEL (Universal)] --> Packs[📦 Language Packs]
    Kernel --> Plugins[🔌 Tool Plugins]
```

### **1. Kernel** (Universal)
Core logic that works for ANY language:
- **ASR Pipeline:** Whisper-based abstraction.
- **Intent Extraction:** LLM-powered, schema-enforced.
- **Decision Engine:** Multi-observer resonance logic.
- **Audit:** Legal-grade traceability.

### **2. Language Packs** (Pluggable)
Pre-configured for supported languages (e.g., `fr-FR`, `ar-DZ`).
- **ASR Models:** Fine-tuned Whisper adapters.
- **Ontology:** Emergency Enums (Fire, Medical).
- **Knowledge:** RAG base for protocols.

### **3. Tool Plugins** (Extensible)
- **Annotation Tool:** Web UI for transcription labeling.
- **Analytics:** Post-call KPI dashboard.

---

## 🎯 Design Principles

1.  **Language-Agnostic Core:** Add new languages without changing the kernel.
2.  **Schema-First:** Strict Pydantic validation (JSON) > Free text. **No hallucinations**.
3.  **Human-in-the-Loop:** AI assists, humans decide on low-confidence cases.
4.  **Audit-First:** Every decision is traceable to source evidence.

---

## 📐 Architecture Overview

ELK follows the **Language Layer** paradigm:

```text
Audio Input
    ↓
[ASR] Whisper (fine-tuned adapter)
    ↓
Transcription
    ↓
[Intent Extraction] LLM (schema-constrained)
    ↓
Structured Intent (JSON)
    ↓
[Decision Engine] Resonance Logic
    ↓
Decision Proposal
    ↓
[Validation] Human-in-the-Loop Check
    ↓
Final Decision & JSON Dispatch
```

[Read full architecture →](docs/architecture.md)

---

## 🚀 Current Status

**Phase:** Implementation & Verification

**Completed:**
- ✅ Core Architecture Definition
- ✅ Kernel Interfaces & Contracts (`elk/kernel/schemas/`)
- ✅ Language Pack Specification
- ✅ Plugin System Design
- ✅ PRD (Product Requirements Document)
- ✅ **FastAPI Engine** (Core Server)
- ✅ **Gemini 1.5 Integration** (Structured LLM)
- ✅ **RAG Engine** (Lexical Search)
- ✅ **Docker Ready** (Air-Gap Deployment)
- ✅ **CI/CD Pipeline** (GitHub Actions)

**In Progress:**
- 🔨 Multi-modal support (Voice-to-JSON)
- 🔨 Advanced Analytics Dashboard
- 🔨 Extended Language Packs (French, Arabizi)

[View detailed roadmap →](docs/roadmap.md)

---

## 📚 Documentation

- **[Vision](docs/vision.md)** - Why ELK exists and what it solves.
- **[Architecture](docs/architecture.md)** - System design deep-dive.
- **[Kernel Design](docs/kernel-design.md)** - Core components and interfaces.
- **[Language Packs](docs/language-packs.md)** - How to create new language support.
- **[Roadmap](docs/roadmap.md)** - Future plans.

---

## 💡 Example Use Cases

### Use Case 1: Emergency Call (France)
```json
{
  "incident_type": "fire",
  "urgency": "critical",
  "location": {"type": "residence", "address": "12 rue de la Paix"},
  "decision": "dispatch_fire_and_ambulance",
  "confidence": 0.94
}
```

---

## 🤝 Contributing

ELK is designed to be community-driven. Code contributions are not yet open as the kernel implementation is in active design phase.
**Star ⭐ the repo to get notified when we open for contributions.**

---

## 📜 License

MIT License - see [LICENSE](LICENSE).

---

**Author:** [Your Name]
*Building the future of Decentralized Emergency Intelligence.*
