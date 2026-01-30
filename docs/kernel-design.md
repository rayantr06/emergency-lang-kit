# ⚙️ Kernel Design: The Core Engine

The **ELK Kernel** is the immutable core of the system. It handles the orchestration of the 5-stage pipeline.

## 1. Core Interfaces (`core/interfaces.py`)

The system relies on strict interfaces to ensure modularity.

### ASR Interface
```python
class ASRProvider(ABC):
    @abstractmethod
    def transcribe(self, audio: bytes, lang_code: str) -> str:
        """
        Transcribes audio to text.
        :param audio: Raw audio bytes.
        :param lang_code: Language code (e.g., 'fr-FR').
        :return: Transcribed text string.
        """
        pass
```

### LLM Interface
```python
class LLMProvider(ABC):
    @abstractmethod
    def predict(self, prompt: str, schema: BaseModel) -> BaseModel:
        """
        Generates a structured prediction strictly adhering to the Pydantic schema.
        :param prompt: The system + user prompt.
        :param schema: The Pydantic class to validate against.
        :return: Instance of the schema.
        """
        pass
```

## 2. The Operational State (`core/schemas.py`)

Every call is represented by an `OperationalState` object that evolves through the pipeline.

```python
class OperationalState(BaseModel):
    call_id: str
    timestamp: datetime
    
    # Ingestion Layer
    transcription: Optional[str] = None
    transcription_confidence: float = 0.0
    
    # Semantic Layer (Intent)
    incident_type: IncidentType  # Enum: FIRE, MEDICAL...
    urgency: UrgencyLevel        # Enum: LOW, HIGH...
    
    # Entity Layer
    location: Optional[LocationEntity]
    casualties: Optional[int]
    
    # Decision Layer
    decision: Optional[DecisionProposal]
    reasoning_trace: str  # Mandatory for audit
```

## 3. Dependency Injection
The Kernel uses a `ServiceContainer` to load plugins dynamically at runtime.
```python
kernel = ElkKernel(
    asr=WhisperAdapter(model_path="packs/fr-FR/model.bin"),
    search=ChromaDBRetriever(index="packs/fr-FR/procedures")
)
```
