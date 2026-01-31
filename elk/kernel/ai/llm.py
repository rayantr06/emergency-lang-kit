import os
import json
import google.generativeai as genai
from typing import Dict, Any, Type
from pydantic import BaseModel
from elk.kernel.schemas.interfaces import EmergencyCall

class LLMClient:
    """
    Client for Google Gemini 1.5 Flash.
    Enforces strict JSON output matching Pydantic schemas.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ WARNING: No GEMINI_API_KEY found. AI features will fail.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"response_mime_type": "application/json"}
            )

    def generate_structured(self, system_prompt: str, user_input: str, response_schema: Type[BaseModel] = EmergencyCall) -> Dict[str, Any]:
        """
        Generates a structured JSON response from the LLM.
        """
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        full_prompt = f"""
        {system_prompt}

        OUTPUT SCHEMA (JSON):
        {response_schema.model_json_schema()}

        INPUT:
        {user_input}
        """

        try:
            response = self.model.generate_content(full_prompt)
            # Parse JSON
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(f"❌ LLM Generation Error: {e}")
            raise e
