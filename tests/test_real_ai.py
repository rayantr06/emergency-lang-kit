import os
import pytest
from elk.kernel.ai.llm import LLMClient
from elk.kernel.schemas.interfaces import EmergencyCall

# Skip if no API key
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API Key found")
def test_real_llm_generation():
    """
    Integration Test: Calls Google Gemini API.
    Verifies that the output matches the Pydantic Schema.
    """
    client = LLMClient()
    
    prompt = "Extract info from: 'There is a fire in Akfadou forest.'"
    
    data = client.generate_structured(
        system_prompt="You are an extractor.",
        user_input=prompt,
        response_schema=EmergencyCall
    )
    
    # Assertions
    assert isinstance(data, dict)
    assert "incident_type" in data
    assert data["incident_type"] == "fire_forest" # Smart enough to map
