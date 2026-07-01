"""
Fine-tuning на Industrial Reasoning Model с Unsloth + QLoRA
============================================================
Изисква: GPU с минимум 16GB VRAM (A100 40GB препоръчано)
Среда:   RunPod / Lambda Labs с Ubuntu 22.04 + CUDA 12.x

Инсталация (изпълни ВЕДНЪЖ в терминала):
  pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
  pip install --no-deps trl peft accelerate bitsandbytes datasets

Използване:
  python finetune_unsloth.py --dataset ./dataset --output ./my_irm_model
"""

import os
import argparse
from pathlib import Path

# ── Зареди библиотеките ───────────────────────────────────────────────────────
try:
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_from_disk
except ImportError:
    raise SystemExit(
        "Инсталирай зависимостите (виж горе в коментарите)."
    )

# ═════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ — промени тук ако е нужно
# ═════════════════════════════════════════════════════════════════════════════

# Базов модел — Llama 3.1 8B е отличен избор за индустриални задачи
BASE_MODEL = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"

# Алтернативи (разкоментирай желания):
# BASE_MODEL = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit"   # по-лек
# BASE_MODEL = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"        # силен при многоезичност

MAX_SEQ_LENGTH = 2048    # максимална дължина на sequence (токени)
DTYPE          = None    # None = автоматично (bfloat16 за A100/H100)
LOAD_IN_4BIT   = True    # QLoRA — зарежда модела в 4-bit за пестене на VRAM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="./dataset",
                        help="Директория с подготвения dataset (от prepare_data.py)")
    parser.add_argument("--output",  type=str, default="./my_irm_model",
                        help="Директория за запис на обучения модел")
    parser.add_argument("--epochs",  type=int, default=3,
                        help="Брой епохи (default: 3)")
    parser.add_argument("--batch",   type=int, default=2,
                        help="Batch size на GPU (default: 2, намали при OOM)")
    parser.add_argument("--lr",      type=float, default=2e-4,
                        help="Learning rate (default: 2e-4)")
    parser.add_argument("--report_to", type=str, default="none",
                        help="Къде да се докладват метриките (none, wandb, tensorboard)")
    parser.add_argument("--lora_r", type=int, default=16,
                        help="LoRA rank (r)")
    args = parser.parse_args()

    # ── 0. Инициализирай WandB ако е нужно ──────────────────────────────────
    if args.report_to == "wandb":
        try:
            import wandb
            wandb.init(project="industrial-reasoning-model", name=f"run-{BASE_MODEL.split('/')[-1]}")
        except ImportError:
            print("⚠️ WandB не е инсталиран. Използвай 'pip install wandb'")
            args.report_to = "none"

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Зареди базовия модел с QLoRA ──────────────────────────────────────
    print(f"\n🔄 Зареждане на базов модел: {BASE_MODEL}")
    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name      = BASE_MODEL,
            max_seq_length  = MAX_SEQ_LENGTH,
            dtype           = DTYPE,
            load_in_4bit    = LOAD_IN_4BIT,
        )
    except Exception as e:
        print(f"❌ КРИТИЧНА ГРЕШКА ПРИ ЗАРЕЖДАНЕ: {e}")
        if "GPU" in str(e) or "accelerator" in str(e):
            print("⚠️ СИСТЕМАТА НЕ ОТКРИВА GPU! Обучението с Unsloth изисква NVIDIA GPU с CUDA.")
        exit(1)

    # ── 2. Конфигурирай LoRA адаптерите ──────────────────────────────────────
    # r=16 е добър баланс качество/скорост; увеличи до 64 за по-добри резултати
    model = FastLanguageModel.get_peft_model(
        model,
        r                   = args.lora_r,
        target_modules      = [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha          = args.lora_r,
        lora_dropout        = 0,       # 0 = оптимизирано от Unsloth
        bias                = "none",
        use_gradient_checkpointing = "unsloth",  # пести VRAM
        random_state        = 42,
        use_rslora          = False,
        loftq_config        = None,
    )

    print(f"✅ LoRA адаптери конфигурирани")
    model.print_trainable_parameters()  # показва % обучаеми параметри (~1-2%)

    # ── 3. Зареди dataset ─────────────────────────────────────────────────────
    print(f"\n📂 Зареждане на dataset от: {args.dataset}")
    dataset = load_from_disk(args.dataset)
    train_data = dataset["train"]
    eval_data  = dataset["test"]
    print(f"   Train: {len(train_data):,} | Validation: {len(eval_data):,}")

    # ── 4. Конфигурирай обучението ────────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir              = str(out_dir / "checkpoints"),
        num_train_epochs        = args.epochs,
        per_device_train_batch_size  = args.batch,
        gradient_accumulation_steps  = 4,
        warmup_steps            = 10,
        learning_rate           = args.lr,
        fp16                    = not FastLanguageModel.is_bfloat16_supported(),
        bf16                    = FastLanguageModel.is_bfloat16_supported(),
        logging_steps           = 5,
        evaluation_strategy     = "steps",
        eval_steps              = 50,
        save_strategy           = "steps",
        save_steps              = 100,
        save_total_limit        = 2,
        optim                   = "adamw_8bit",
        weight_decay            = 0.01,
        lr_scheduler_type       = "cosine",
        seed                    = 42,
        report_to               = args.report_to,
        load_best_model_at_end  = True,  # За Early Stopping
    )

    # ── 5. Инициализирай trainer-а ────────────────────────────────────────────
    from transformers import EarlyStoppingCallback
    
    trainer = SFTTrainer(
        model           = model,
        tokenizer       = tokenizer,
        train_dataset   = train_data,
        eval_dataset    = eval_data,
        dataset_text_field = "text",
        max_seq_length  = MAX_SEQ_LENGTH,
        dataset_num_proc = 2,
        args            = training_args,
        callbacks       = [EarlyStoppingCallback(early_stopping_patience=3)]
    )

    # ── 6. СТАРТ НА ОБУЧЕНИЕТО ────────────────────────────────────────────────
    print(f"\n🚀 Старт на обучението...")
    print(f"   Епохи: {args.epochs} | Batch: {args.batch} | LR: {args.lr}")
    print(f"   Следи loss — трябва да намалява стабилно\n")

    trainer_stats = trainer.train()

    print(f"\n✅ Обучението завърши!")
    print(f"   Продължителност: {trainer_stats.metrics['train_runtime']:.0f} секунди")
    print(f"   Финален loss:    {trainer_stats.metrics['train_loss']:.4f}")

    # ── 7. Запази модела в GGUF формат за Ollama ──────────────────────────────
    print(f"\n💾 Запис на модела...")

    # Запази LoRA адаптерите (малки — само промените)
    lora_path = str(out_dir / "lora_adapters")
    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)
    print(f"   LoRA адаптери: {lora_path}")

    # Запази в GGUF формат за Ollama (16-bit за по-добро качество)
    gguf_path = str(out_dir / "model_q8.gguf")
    print(f"   Конвертиране в GGUF (q8_0)...")
    model.save_pretrained_gguf(
        str(out_dir / "gguf"),
        tokenizer,
        quantization_method = "q8_0",   # q8_0 = добро качество, ~8GB файл
        # Алтернативи:
        # "q4_k_m"  → ~4GB, малко по-ниско качество, по-бързо
        # "f16"     → ~16GB, максимално качество
    )

    print(f"\n🎉 Готово! Твоят Industrial Reasoning Model е запазен в: {out_dir}")
    print(f"\n📋 Следваща стъпка — импорт в Ollama:")
    print(f"   Виж: deploy_ollama.sh")


if __name__ == "__main__":
    main()
