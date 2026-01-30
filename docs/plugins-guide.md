# 🔌 Plugins Guide: Building Tools

ELK allows developers to build "Tools" that sit on top of the Kernel/Packs.

## What is a Tool?
A tool is a Python script or application that interacts with `core.ElkKernel`.
Examples: Annotation UIs, Analytics Dashboards, Simulators.

## Architecture
Tools reside in the `tools/` directory.

```text
tools/
├── analyzer/          # Example: Analytics Dashboard
│   ├── app.py         # Entry point
│   └── requirements.txt
└── annotator/         # Example: Labeling Tool
    ├── app.py
    └── utils.py
```

## Tutorial: Building a Simple "Ping" Tool

1.  **Create directory:** `tools/ping-bot/`
2.  **Create script:** `main.py`

```python
from core.kernel import ElkKernel
from core.schemas import OperationalState

def run_ping_check():
    # Initialize Kernel (Mock)
    kernel = ElkKernel()
    
    # Simulate a Call State
    state = OperationalState(
        call_id="test-123",
        transcription="This is a test call."
    )
    
    # Run Pipeline
    result = kernel.process(state)
    print(f"Processed Call: {result.json()}")

if __name__ == "__main__":
    run_ping_check()
```

## Standard Tools Provided
*   **`elk-annotate`**: Streamlit app for correcting transcripts.
*   **`elk-train`**: Wrapper for Unsloth/QLoRA training.
*   **`elk-scaffold`**: Project generator.
