# 🗺️ Project Roadmap: Building the "Factory"

This roadmap covers the journey from a Core Engine to a fully distributed "Community Factory".

## ✅ Phase 1: The Foundation (Kernel Stability)
> **Goal:** A solid, deterministic engine that can execute a pipeline.
- [x] **Ontology Definition:** Strict Pydantic Models for `EmergencyCall` and `OperationalState`.
- [x] **Pipeline Architecture:** Design of the 5-stage Semantic-Kinetic-Dynamic flow.
- [x] **Documentation Suite:** PRD, Architecture, and Master Vision frozen.

## 🚧 Phase 2: The Factory Tooling (Enabling Scale)
> **Goal:** Build the tools that build the packs.
- [ ] **CLI Entry Point:** `elk` command line interface.
- [ ] **Scaffolder:** `elk scaffold` to generate standard folder structures.
- [ ] **Annotator:** `elk annotate` (Streamlit) for audio-to-text correction.
- [ ] **Extractor:** `elk extract` (LangChain) for parsing PDF Protocols into Rules.

## 🟡 Phase 3: The First Vertical (Proof of Concept)
> **Goal:** Create `pack-kabyle-dz` to prove the architecture.
- [ ] **Data Collection:** Collect/Generate 100 Kabyle/Arabizi samples.
- [ ] **Training:** Use `elk train` (Unsloth) to create `adapter.bin`.
- [ ] **Rules:** Implement DGPC (Protection Civile) rules in YAML.
- [ ] **End-to-End Test:** Process a full call from Audio to JSON Dispatch.

## 🔵 Phase 4: Operational Intelligence (Analytics)
> **Goal:** Turn the logs into value.
- [ ] **Data Warehouse:** Implement SQLite/JSONL logging in `core/analytics.py`.
- [ ] **Dashboard:** Simple Analytics UI (Streamlit) showing Call Heatmaps.
- [ ] **KPI Reporter:** Automated "Daily Briefing" generator.

## 🟣 Phase 5: Enterprise Hardening (Future)
- [ ] **Hybrid RAG:** Implement BM25 + Vector Search.
- [ ] **Dockerization:** Full `docker-compose.yml` for Air-Gapped deployment.
- [ ] **Real-Time Streaming:** VAD-triggered chunking via WebSockets.
