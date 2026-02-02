"""
ELK Factory - Dynamic Pipeline Loader
Loads Language Pack pipelines at runtime using the Factory Pattern.
"""

import importlib
from typing import Dict, Any, Optional
from elk.engine.pipeline.base_pipeline import BasePipeline


def load_pipeline(pack_name: str, config: Optional[Dict[str, Any]] = None) -> BasePipeline:
    """
    Dynamically load a Language Pack's pipeline.
    
    Args:
        pack_name: Pack identifier (e.g., "dz-kab-protection")
        config: Configuration dict to pass to pipeline
        
    Returns:
        Initialized pipeline instance
        
    Raises:
        ValueError: If pack not found or no Pipeline class exists
    """
    # Convert pack name to valid Python module name
    module_name = pack_name.replace("-", "_")
    module_path = f"packs.{module_name}.runtime.pipeline"
    
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise ValueError(f"Pack not found: {pack_name}. Error: {e}")
    
    # Find Pipeline class (convention: class name ends with 'Pipeline')
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, BasePipeline) and 
            obj is not BasePipeline):
            return obj(config or {})
    
    raise ValueError(f"No Pipeline class found in pack: {pack_name}")


def list_available_packs() -> list[str]:
    """List all installed language packs."""
    import os
    packs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "packs")
    if os.path.exists(packs_dir):
        return [d for d in os.listdir(packs_dir) 
                if os.path.isdir(os.path.join(packs_dir, d)) and not d.startswith("_")]
    return []
