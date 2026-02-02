"""
ELK Training - Unsloth QLoRA Trainer
Wrapper for fine-tuning Whisper with Unsloth.
Per MASTER_VISION 4.4: elk train command.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class LoRAConfig:
    """LoRA configuration per MASTER_VISION spec."""
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: tuple = ("q_proj", "v_proj")


@dataclass
class TrainingConfig:
    """Training configuration."""
    base_model: str = "openai/whisper-large-v3"
    output_dir: str = "./output"
    
    # Training hyperparameters
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 4
    
    # LoRA config
    lora: LoRAConfig = None
    
    # Compute
    fp16: bool = True
    gradient_checkpointing: bool = True
    
    def __post_init__(self):
        if self.lora is None:
            self.lora = LoRAConfig()


class UnslothTrainer:
    """
    Unsloth-based Whisper fine-tuning trainer.
    
    Provides 2x faster training with 60% less memory.
    Designed for Colab Free Tier (T4 GPU).
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self._model = None
        self._tokenizer = None
        self._peft_model = None
    
    def check_dependencies(self) -> bool:
        """Check if all required packages are installed."""
        required = ['unsloth', 'transformers', 'peft', 'trl', 'torch']
        missing = []
        
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        
        if missing:
            logger.error(f"Missing packages: {missing}")
            logger.error("Install with: pip install unsloth transformers peft trl torch")
            return False
        
        return True
    
    def load_model(self):
        """Load base model with Unsloth optimizations."""
        if not self.check_dependencies():
            raise ImportError("Required packages not installed")
        
        from unsloth import FastWhisperModel
        
        logger.info(f"Loading model: {self.config.base_model}")
        
        self._model, self._tokenizer = FastWhisperModel.from_pretrained(
            self.config.base_model,
            load_in_4bit=True,
            dtype=None
        )
        
        # Apply LoRA
        self._peft_model = FastWhisperModel.get_peft_model(
            self._model,
            r=self.config.lora.r,
            lora_alpha=self.config.lora.lora_alpha,
            lora_dropout=self.config.lora.lora_dropout,
            target_modules=list(self.config.lora.target_modules)
        )
        
        logger.info("Model loaded with LoRA applied")
        return self
    
    def prepare_dataset(
        self,
        train_path: str,
        test_path: Optional[str] = None
    ):
        """
        Prepare dataset for training.
        Expects JSONL with 'audio' and 'sentence' keys.
        """
        from datasets import load_dataset, Audio
        
        logger.info(f"Loading dataset from: {train_path}")
        
        dataset = load_dataset('json', data_files={
            'train': train_path,
            'test': test_path
        } if test_path else {'train': train_path})
        
        # Cast audio column
        dataset = dataset.cast_column('audio', Audio(sampling_rate=16000))
        
        self._dataset = dataset
        logger.info(f"Dataset prepared: {len(dataset['train'])} training samples")
        return self
    
    def train(self) -> Dict[str, Any]:
        """
        Run training with Unsloth optimizations.
        Returns training metrics.
        """
        if self._peft_model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        if self._dataset is None:
            raise ValueError("Dataset not prepared. Call prepare_dataset() first.")
        
        from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        training_args = Seq2SeqTrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            fp16=self.config.fp16,
            gradient_checkpointing=self.config.gradient_checkpointing,
            evaluation_strategy="steps" if 'test' in self._dataset else "no",
            eval_steps=500,
            save_steps=500,
            logging_steps=100,
            save_total_limit=2,
            predict_with_generate=True,
            generation_max_length=225,
            report_to=["tensorboard"]
        )
        
        trainer = Seq2SeqTrainer(
            model=self._peft_model,
            args=training_args,
            train_dataset=self._dataset['train'],
            eval_dataset=self._dataset.get('test'),
            tokenizer=self._tokenizer
        )
        
        logger.info("Starting training...")
        result = trainer.train()
        
        metrics = {
            'loss': result.training_loss,
            'steps': result.global_step,
            'runtime_seconds': result.metrics.get('train_runtime', 0)
        }
        
        logger.info(f"Training complete: {metrics}")
        return metrics
    
    def save_adapter(self, pack_path: str) -> str:
        """
        Save LoRA adapter to pack models folder.
        Returns path to saved adapter.
        """
        if self._peft_model is None:
            raise ValueError("No trained model to save")
        
        models_dir = Path(pack_path) / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        adapter_path = models_dir / "whisper-lora-adapter"
        
        self._peft_model.save_pretrained(str(adapter_path))
        logger.info(f"Adapter saved to: {adapter_path}")
        
        # Also save config for reproducibility
        config_path = adapter_path / "training_config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'base_model': self.config.base_model,
                'lora_r': self.config.lora.r,
                'lora_alpha': self.config.lora.lora_alpha,
                'epochs': self.config.num_epochs,
                'batch_size': self.config.batch_size
            }, f, indent=2)
        
        return str(adapter_path)


def train_pack(
    pack_name: str,
    dataset_path: str,
    base_model: str = "openai/whisper-large-v3",
    epochs: int = 3
) -> Dict[str, Any]:
    """
    High-level function to train a pack.
    Used by elk train CLI command.
    """
    from elk.factory.config import load_pack_config
    
    # Load pack config
    pack_config = load_pack_config(pack_name)
    pack_path = pack_config.pack_path
    
    # Setup training config
    config = TrainingConfig(
        base_model=base_model,
        output_dir=str(pack_path / "models" / "training_output"),
        num_epochs=epochs
    )
    
    # Train
    trainer = UnslothTrainer(config)
    trainer.load_model()
    trainer.prepare_dataset(dataset_path)
    metrics = trainer.train()
    
    # Save adapter
    adapter_path = trainer.save_adapter(str(pack_path))
    
    return {
        'status': 'success',
        'metrics': metrics,
        'adapter_path': adapter_path
    }
