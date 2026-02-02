"""
ELK Kernel - LLM Client with Retry Logic
Implements robust cloud/local toggle with exponential backoff.
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Use orjson for 3-10x faster JSON parsing (with fallback)
try:
    import orjson
    def json_loads(s): return orjson.loads(s)
    def json_dumps(obj): return orjson.dumps(obj).decode()
except ImportError:
    import json
    json_loads = json.loads
    json_dumps = json.dumps


logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
    
    @abstractmethod
    def _call_api(self, prompt: str, system_prompt: str) -> str:
        """Make the actual API call. Implement in subclass."""
        pass
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate response with retry logic.
        Uses exponential backoff for transient failures.
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return self._call_api(prompt, system_prompt)
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.retry_config.max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.retry_config.base_delay_seconds * (
                            self.retry_config.exponential_base ** attempt
                        ),
                        self.retry_config.max_delay_seconds
                    )
                    
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
        
        # All retries exhausted
        logger.error(f"LLM call failed after {self.retry_config.max_retries + 1} attempts")
        raise last_exception


class GeminiClient(BaseLLMClient):
    """
    Google Gemini API client with retry support.
    Cloud LLM for high performance.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        retry_config: Optional[RetryConfig] = None
    ):
        super().__init__(retry_config)
        
        # Store for lazy validation
        self._api_key = api_key
        self.model = model
        self._client = None
    
    @property
    def api_key(self) -> str:
        """Get API key, raising error only when actually needed."""
        key = self._api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY required. Set env variable or pass api_key parameter."
            )
        return key
    
    def _get_client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client
    
    def _call_api(self, prompt: str, system_prompt: str) -> str:
        """Make Gemini API call."""
        client = self._get_client()
        
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = client.generate_content(full_prompt)
        return response.text


class OllamaClient(BaseLLMClient):
    """
    Ollama client for local/air-gapped deployment.
    Implements FR-06: Air-Gapped Capable.
    """
    
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 60,
        retry_config: Optional[RetryConfig] = None
    ):
        super().__init__(retry_config)
        
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        
        # Reuse HTTP session for connection pooling (performance)
        import requests
        self._session = requests.Session()
    
    def _call_api(self, prompt: str, system_prompt: str) -> str:
        """Make Ollama API call with session reuse."""
        response = self._session.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            },
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json().get("response", "")


class LLMClient:
    """
    Unified LLM client with Cloud/Local toggle.
    Implements FR-06 from PRD.
    
    Usage:
        client = LLMClient()  # Auto-detects from LLM_PROVIDER env
        response = client.generate("Extract entities from: ...")
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        # Determine provider from env or explicit
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        
        # Default retry config
        retry = retry_config or RetryConfig(
            max_retries=3,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0
        )
        
        # Initialize appropriate client
        if self.provider == "gemini":
            self._client = GeminiClient(retry_config=retry)
        elif self.provider == "ollama":
            model = os.getenv("OLLAMA_MODEL", "llama3")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self._client = OllamaClient(
                model=model,
                base_url=base_url,
                retry_config=retry
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
        
        logger.info(f"LLM Client initialized: provider={self.provider}")
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using configured provider."""
        return self._client.generate(prompt, system_prompt)
    
    def extract_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Generate and parse JSON response.
        Implements FR-03: Strict JSON output.
        """
        response = self.generate(prompt, system_prompt)
        
        # Clean response (remove markdown code blocks if present)
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json_loads(text.strip())
    
    def generate_structured(
        self,
        system_prompt: str,
        user_input: str,
        response_schema: Any = None
    ) -> Dict[str, Any]:
        """
        Generate structured output with optional Pydantic schema validation.
        
        Args:
            system_prompt: System context
            user_input: User transcription/input
            response_schema: Pydantic model for validation (optional)
            
        Returns:
            Validated dict matching schema
        """
        # Enhance prompt with JSON requirement
        enhanced_system = f"""{system_prompt}

IMPORTANT: Respond with valid JSON only. No markdown, no explanation.
"""
        
        # Generate and parse JSON
        data = self.extract_json(user_input, enhanced_system)
        
        # Validate with Pydantic schema if provided
        if response_schema is not None:
            try:
                # Try to use Pydantic model for validation
                if hasattr(response_schema, 'model_validate'):
                    # Pydantic v2
                    validated = response_schema.model_validate(data)
                    return validated.model_dump()
                elif hasattr(response_schema, 'parse_obj'):
                    # Pydantic v1
                    validated = response_schema.parse_obj(data)
                    return validated.dict()
            except Exception as e:
                logger.warning(f"Schema validation failed: {e}. Returning raw dict.")
        
        return data

