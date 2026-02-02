# 🗺️ Project Roadmap

This roadmap outlines the development phases of the Emergency Lang Kit ecosystem.

## ✅ Phase 1: The Foundation (Architecture)
> **Refining the Kernel & Specifications**
- [x] **Ontology Definition:** Strict Pydantic Models for `EmergencyCall` and `OperationalState`.
- [x] **Pipeline Architecture:** Design of the 5-stage Semantic-Kinetic-Dynamic flow.
- [x] **Documentation Suite:** PRD, Architecture, and Master Vision frozen.

## ✅ Phase 2: The Factory Tooling
> **Building the tools to scale content creation**
- [x] **CLI Entry Point:** `elk` command line interface.
- [x] **Scaffolder:** `elk scaffold` to generate standard folder structures.
- [x] **Annotator:** `elk annotate` (Streamlit) for audio-to-text correction.
- [x] **Extractor:** `elk extract` (LangChain) for parsing PDF Protocols into Rules.

## 🟡 Phase 3: The First Vertical (PoC)
> **Proof of Concept: Kabyle Civil Protection**
- [ ] **Data Collection:** Collect/Generate 100 Kabyle/Arabizi samples.
- [ ] **Training:** Use `elk train` (Unsloth) to create `adapter.bin`.
- [ ] **Integration:** End-to-End test call processing.

## 🔵 Phase 4: Operational Intelligence
> **Analytics & Data Warehousing**
- [ ] **Data Warehouse:** SQLite/JSONL logging implementation.
- [ ] **Dashboard:** Heatmap visualization of incidents.

## ✅ Phase 5: Prototype Hardening (Completed)
> **Sécurité et résilience pour portfolio/demo**
- [x] **Auth:** `X-API-Key` middleware, CORS/AllowedHosts stricts.
- [x] **Backpressure:** Redis queue depth limiter (429 Too Many Requests).
- [x] **Traçabilité:** `correlation_id` propagé API → Worker → Connector.
- [x] **Ops:** Docker non-root (`elkuser`), health check étendu, background cleanup.
- [x] **Tests:** Suite 5/5 (sécurité, backpressure, API core). Voir `docs/TEST_RESULTS.md`.

---

## 🚧 Phase 6: Production Readiness (Next)
> **Pour passer d'un prototype durci à une posture "prod"**
- [ ] **Identity & Access:** OIDC/mTLS, rate limiting/quotas côté edge.
- [ ] **Observabilité:** OTel + métriques Prometheus (latence, queue depth, retries) + alerting.
- [ ] **Data Lifecycle:** Dead Letter Queue, idempotence des jobs/connectors.
- [ ] **HA:** Redis/DB en HA, déploiement K8s avec HPA basé sur la profondeur de queue.
- [ ] **Governance:** Hash/signature des packs/modèles, validation au démarrage, chiffrement des secrets/PII.
