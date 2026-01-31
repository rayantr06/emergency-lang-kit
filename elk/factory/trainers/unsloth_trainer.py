"""
ELK Factory - Unsloth Trainer
Master Thesis 2026 - Qwen 2.5 (7B) + LoRA
Migrated from: ml_pipeline/notebooks/colab_training_script.py
"""

# ==========================================
# 1. SETUP (Colab Install Command)
# ==========================================
# !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
# !pip install --no-deps "xformers<0.0.27" "trl<0.8.0" peft accelerate bitsandbytes

from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import json

class ELKTrainer:
    def __init__(self, dataset_path: str, model_name: str = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"):
        self.dataset_path = dataset_path
        self.model_name = model_name
        self.max_seq_length = 2048
        self.dtype = None # Auto
        self.load_in_4bit = True
        
        # Load Model
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = self.model_name,
            max_seq_length = self.max_seq_length,
            dtype = self.dtype,
            load_in_4bit = self.load_in_4bit,
        )
        
        # Configure LoRA
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r = 16,
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha = 16,
            lora_dropout = 0,
            bias = "none",
            use_gradient_checkpointing = "unsloth",
            random_state = 3407,
            use_rslora = False,
            loftq_config = None,
        )

    def train(self, output_dir: str = "outputs"):
        # Format Data
        alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""
        EOS_TOKEN = self.tokenizer.eos_token
        
        def formatting_prompts_func(examples):
            instructions = examples["instruction"]
            inputs       = examples["input"]
            outputs      = examples["output"]
            texts = []
            for instruction, input, output in zip(instructions, inputs, outputs):
                text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
                texts.append(text)
            return { "text" : texts, }

        dataset = load_dataset("json", data_files=self.dataset_path, split="train")
        dataset = dataset.map(formatting_prompts_func, batched = True)
        
        # Trainer
        trainer = SFTTrainer(
            model = self.model,
            tokenizer = self.tokenizer,
            train_dataset = dataset,
            dataset_text_field = "text",
            max_seq_length = self.max_seq_length,
            dataset_num_proc = 2,
            packing = False,
            args = TrainingArguments(
                per_device_train_batch_size = 2,
                gradient_accumulation_steps = 4,
                warmup_steps = 5,
                max_steps = 60, 
                learning_rate = 2e-4,
                fp16 = not torch.cuda.is_bf16_supported(),
                bf16 = torch.cuda.is_bf16_supported(),
                logging_steps = 1,
                optim = "adamw_8bit",
                weight_decay = 0.01,
                lr_scheduler_type = "linear",
                seed = 3407,
                output_dir = output_dir,
            ),
        )
        
        print("🚀 ELK Trainer: Starting Training...")
        trainer.train()
        print("🏆 ELK Trainer: Training Complete!")

if __name__ == "__main__":
    # Example Usage
    trainer = ELKTrainer("seed_v1.json")
    trainer.train()
