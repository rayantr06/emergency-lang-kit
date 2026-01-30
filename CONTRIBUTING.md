# 🤝 Contributing to Emergency Lang Kit

Welcome to the **Emergency Lang Kit** factory. We are building a critical system, so our contribution standards are high. We prioritize **Safety**, **Readability**, and **Modularity**.

## 🧠 Philosophy: "Architecture First"
1.  **Strict Typing:** Everything must be typed. No `Any` unless absolutely necessary.
2.  **No Magic Strings:** Use Enums for everything (Incidents, Urgency, Actions).
3.  **Human in the Loop:** Always design for a human operator validation step.

## 🏭 How to Contribute

### Level 1: The "Knowledge Engineer" (No Code)
*   **Add a Domain:** Create a new `domains/{domain_name}/enums.yaml` file to define new incident types or resources.
*   **Add a Rule:** Update `domains/{domain_name}/rules.yaml` to define dispatch logic (e.g., "If Fire, Dispatch Truck").

### Level 2: The "Linguist" (Low Code)
*   **Add a Language:** Fork the repo and duplicate `languages/_template/`.
*   **Translate:** Provide the `grammar.md` and basic prompts for your dialect.
*   **Annotate:** Help us label audio samples using the Annotation Tool (Phase 3).

### Level 3: The "System Architect" (Code)
*   Integrate a new ASR provider (e.g., Deepgram, google-speech).
*   Optimize the Vector DB retrieval (RAG).
*   Improve the core State Machine logic.

## 🛠️ Development Setup

```bash
# 1. Clone your fork
git clone https://github.com/YOUR_USERNAME/emergency-lang-kit.git

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Run tests before pushing
pytest tests/
```

## 📜 Pull Request Process
1.  Ensure all new code is covered by tests.
2.  Update the `README.md` if you change public interfaces.
3.  **Core Principle:** If you add a feature, you must add the corresponding **Validation Logic** in the Schema.
