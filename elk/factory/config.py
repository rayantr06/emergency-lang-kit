"""
ELK Factory - Pack Configuration Loader
Loads and validates pack configuration from YAML files.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class PackConfig:
    """
    Loads and provides access to pack configuration.
    
    Supports:
    - config.yaml: LLM, ASR, RAG, and general settings
    - rules.yaml: Business decision rules
    - geography.json: GeoJSON spatial data
    """
    
    def __init__(self, pack_path: str):
        import yaml
        import json
        
        self.pack_path = Path(pack_path)
        
        # Load config.yaml
        config_file = self.pack_path / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}
        
        # Load rules.yaml
        rules_file = self.pack_path / "rules.yaml"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                self._rules = yaml.safe_load(f)
        else:
            self._rules = {}
        
        # Load geography.json
        geo_file = self.pack_path / "geography.json"
        if geo_file.exists():
            with open(geo_file, 'r', encoding='utf-8') as f:
                self._geography = json.load(f)
        else:
            self._geography = {}
        
        # Expand environment variables
        self._expand_env_vars(self._config)
    
    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in config values."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._expand_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._expand_env_vars(item)
        elif isinstance(obj, str) and obj.startswith("${") and "}" in obj:
            # Parse ${VAR:-default} syntax
            var_expr = obj[2:-1]  # Remove ${ and }
            if ":-" in var_expr:
                var_name, default = var_expr.split(":-", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, obj)
        return obj
    
    @property
    def pack_name(self) -> str:
        return self._config.get("pack", {}).get("name", "unknown")
    
    @property
    def version(self) -> str:
        return self._config.get("pack", {}).get("version", "0.0.0")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key (e.g., 'llm.provider')."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for Cloud/Local toggle."""
        llm = self._config.get("llm", {})
        provider = llm.get("provider", "gemini")
        
        if provider == "gemini":
            return {
                "provider": "gemini",
                "model": llm.get("cloud", {}).get("model", "gemini-1.5-flash"),
                "api_key": llm.get("cloud", {}).get("api_key")
            }
        else:
            return {
                "provider": "ollama",
                "model": llm.get("local", {}).get("model", "llama3"),
                "base_url": llm.get("local", {}).get("base_url", "http://localhost:11434")
            }
    
    def get_asr_config(self) -> Dict[str, Any]:
        """Get ASR configuration for WhisperX."""
        return self._config.get("asr", {})
    
    def get_rag_config(self) -> Dict[str, Any]:
        """Get RAG configuration."""
        return self._config.get("rag", {})
    
    def get_confidence_config(self) -> Dict[str, Any]:
        """Get confidence calculator configuration."""
        return self._config.get("confidence", {})
    
    @property
    def rules(self) -> Dict[str, Any]:
        """Get business rules."""
        return self._rules
    
    @property
    def geography(self) -> Dict[str, Any]:
        """Get geography GeoJSON data."""
        return self._geography
    
    def get_communes(self) -> list:
        """Extract commune names from geography."""
        communes = []
        for feature in self._geography.get("features", []):
            props = feature.get("properties", {})
            if props.get("type") == "commune":
                communes.append(props.get("name"))
        return communes
    
    def get_landmarks(self) -> list:
        """Extract landmark names from geography."""
        landmarks = []
        for feature in self._geography.get("features", []):
            props = feature.get("properties", {})
            if props.get("type") == "landmark":
                landmarks.append(props.get("name"))
        return landmarks


def load_pack_config(pack_name: str) -> PackConfig:
    """
    Load pack configuration by name.
    Searches in the packs/ directory.
    """
    # Convert hyphen to underscore for Python module compatibility
    module_name = pack_name.replace("-", "_")
    
    # Get packs directory
    base_dir = os.getenv("ELK_PACKS_DIR")
    if not base_dir:
        # Default: look in project root's packs/ folder
        # Go up from elk/factory/ to project root
        project_root = Path(__file__).parent.parent.parent
        base_dir = project_root / "packs"
    else:
        base_dir = Path(base_dir)
    
    pack_path = base_dir / module_name
    
    if not pack_path.exists():
        raise FileNotFoundError(f"Pack not found: {pack_name} at {pack_path}")
    
    return PackConfig(pack_path)
