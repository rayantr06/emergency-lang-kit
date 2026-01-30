# 📦 Language Packs: Adding New Languages

To add support for a new language (e.g., Catalan, Kabyle, Cree), you do NOT modify the codebase. You create a **Language Pack**.

## Pack Structure
A pack is a directory inside `packs/` matching the ISO language code (e.g., `packs/kab-DZ/`).

```text
packs/kab-DZ/
├── config.yaml          # Manifest
├── enums/               # Vocabulary mapping
│   ├── incident.yaml    # Mapping "Tamesrifegt" -> "FIRE"
│   └── urgency.yaml     # Mapping "Urgent" -> "HIGH"
├── models/
│   └── adapter.bin      # QLoRA weights for Whisper (Optional)
├── rag/
│   └── protocols.pdf    # PDF documents for the RAG engine
└── prompts/
    └── system.txt       # "You are a Kabyle emergency operator..."
```

## 1. The Manifest (`config.yaml`)
```yaml
name: "Kabyle Civil Protection"
code: "kab-DZ"
version: "1.0.0"
maintainer: "Team Bejaia"
asr_model: "openai/whisper-large-v3"
adapter_path: "./models/adapter.bin"
```

## 2. Enum Mapping
ELK uses internal Enums (e.g., `FIRE`). The pack maps local words to these Enums.

**`enums/incident.yaml`**:
```yaml
FIRE:
  - "tamesrifegt"
  - "timess"
  - "lkanoun"

MEDICAL:
  - "aṭan"
  - "uvriḍ"
  - "accident"
```

## 3. Creating a Pack
Use the CLI tool to scaffold a new pack:
```bash
elk scaffold pack --name="Kabyle" --code="kab-DZ"
```
