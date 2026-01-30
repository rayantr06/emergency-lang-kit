# 🗺️ Project Roadmap

This roadmap outlines the development phases of the Emergency Lang Kit ecosystem.

## ✅ Phase 1: The Foundation (Architecture)
> **Refining the Kernel & Specifications**
- [x] **Ontology Definition:** Strict Pydantic Models for `EmergencyCall` and `OperationalState`.
- [x] **Pipeline Architecture:** Design of the 5-stage Semantic-Kinetic-Dynamic flow.
- [x] **Documentation Suite:** PRD, Architecture, and Master Vision frozen.

## 🚧 Phase 2: The Factory Tooling (Current Focus)
> **Building the tools to scale content creation**
- [ ] **CLI Entry Point:** `elk` command line interface.
- [ ] **Scaffolder:** `elk scaffold` to generate standard folder structures.
- [ ] **Annotator:** `elk annotate` (Streamlit) for audio-to-text correction.
- [ ] **Extractor:** `elk extract` (LangChain) for parsing PDF Protocols into Rules.

## 🟡 Phase 3: The First Vertical (PoC)
> **Proof of Concept: Kabyle Civil Protection**
- [ ] **Data Collection:** Collect/Generate 100 Kabyle/Arabizi samples.
- [ ] **Training:** Use `elk train` (Unsloth) to create `adapter.bin`.
- [ ] **Integration:** End-to-End test call processing.

## 🔵 Phase 4: Operational Intelligence
> **Analytics & Data Warehousing**
- [ ] **Data Warehouse:** SQLite/JSONL logging implementation.
- [ ] **Dashboard:** Heatmap visualization of incidents.

## 🟣 Phase 5: Enterprise Hardening
- [ ] **Hybrid RAG:** Vector + Keyword Search.
- [ ] **Docker:** Air-gapped deployment capability.
- [ ] **Streaming:** WebSocket implementation for real-time transcription.
