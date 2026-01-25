"""
Fine-tune GPT-2 (small or medium) to generate personalised typing feedback.
Optimised for a 2020-2022 MacBook Air (8 GB, Apple M-series GPU).

Dataset file : typing_feedback_dataset.json
Out-model dir: typing_feedback_final_model

Requires  :  pip install "transformers>=4.40" datasets accelerate sentencepiece
"""

from __future__ import annotations
from pathlib import Path
from typing import List
import json, random, argparse, inspect, sys, torch
from datasets import Dataset
from transformers import (
    GPT2Tokenizer, GPT2LMHeadModel,
    TrainingArguments, Trainer,
    EarlyStoppingCallback, DataCollatorForLanguageModeling,
)

# ──────────────────────────────── CLI ────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--model_size", choices=["small", "medium"], default="medium",
                    help="`small` → gpt2 (124 M) `medium` → gpt2-medium (355 M)")
opt = parser.parse_args()

BASE_MODEL = "gpt2-medium" if opt.model_size == "medium" else "gpt2"
print(f"🏋️  base model  : {BASE_MODEL}")

# ───────────────────────────── config ────────────────────────────────
DATA_PATH   = Path("typing_feedback_dataset.json")
OUT_DIR     = Path("typing_feedback_final_model")
MAX_LEN     = 192                       # 192 tokens fits batch-2 on 8 GB
EPOCHS      = 8                         # early-stop will finish sooner
REAL_BATCH  = 2                         # physical batch per step
GRAD_ACCUM  = 8                         # 2 × 8 = effective 16
LR          = 3e-5
SEED        = 42
SPECIAL_TOK = ["<BOS_FB>", "<EOS_FB>"]

random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

# ──────────────────────── 1 Load & tidy data ────────────────────────
if not DATA_PATH.exists():
    sys.exit(f"❌  {DATA_PATH} not found")

raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
prompts, targets = [], []

for ex in raw:
    fb_lines = ex["feedback"] if isinstance(ex["feedback"], list) else ex["feedback"].splitlines()
    seen: set[str] = set()
    bullets: List[str] = []
    for ln in fb_lines:
        clean = ln.lstrip("💡-• ").strip()
        if clean and clean not in seen:
            seen.add(clean)
            bullets.append(f"- {clean}")
    targets.append("<BOS_FB>\n" + "\n".join(bullets) + "\n<EOS_FB>")
    prompts.append(
        f"Skill Level: {ex['skill_level']}\n"
        f"Original Text: {ex['original_text']}\n"
        f"Typed Text: {ex['typed_text']}\n"
        f"Feedback:\n"
    )

ds = Dataset.from_dict({"prompt": prompts, "target": targets})
print(f"📚  dataset size : {len(ds):,}")

# ───────────────────── 2 Tokenizer & encoding ───────────────────────
tok = GPT2Tokenizer.from_pretrained(BASE_MODEL)
tok.add_special_tokens({"additional_special_tokens": SPECIAL_TOK})
tok.pad_token = tok.eos_token      # reuse <|endoftext|> as PAD

def encode(row):
    merged = row["prompt"] + row["target"]
    enc = tok(merged, padding="max_length", truncation=True, max_length=MAX_LEN)
    prompt_len = len(tok(row["prompt"]).input_ids)
    labels = [-100] * prompt_len + enc["input_ids"][prompt_len:]
    enc["labels"] = labels[:MAX_LEN]
    return enc

train_ds, val_ds = ds.train_test_split(test_size=0.15, seed=SEED).values()
train_ds = train_ds.map(encode, remove_columns=ds.column_names)
val_ds   = val_ds  .map(encode, remove_columns=ds.column_names)

# ───────────────────────── 3 Model ──────────────────────────────────
model = GPT2LMHeadModel.from_pretrained(BASE_MODEL)
model.resize_token_embeddings(len(tok))

device = "mps" if torch.backends.mps.is_available() else "cpu"
model.to(device)
print("⚡  device       :", device)

# ──────────────────── 4 TrainingArguments (compat) ──────────────────
ta_pars = inspect.signature(TrainingArguments.__init__).parameters
new_api = "evaluation_strategy" in ta_pars and "metric_for_best_model" in ta_pars

common_args = dict(
    output_dir                 = OUT_DIR,
    overwrite_output_dir       = True,
    num_train_epochs           = EPOCHS,
    per_device_train_batch_size= REAL_BATCH,
    per_device_eval_batch_size = REAL_BATCH,
    gradient_accumulation_steps= GRAD_ACCUM,
    learning_rate              = LR,
    seed                       = SEED,
    fp16                       = False,
    bf16                       = False,
    dataloader_pin_memory      = False,
    report_to                  = "none",
)

if new_api:
    common_args.update(
        evaluation_strategy      = "epoch",
        save_strategy            = "epoch",
        load_best_model_at_end   = True,
        save_total_limit         = 2,
        metric_for_best_model    = "eval_loss",   # 🔑 EarlyStopping needs this
        greater_is_better        = False,
        lr_scheduler_type        = "cosine",
        warmup_ratio             = 0.04,
    )
else:
    print("📦  legacy transformers detected – falling back to minimal args")
    common_args.update(save_steps=0)

args = TrainingArguments(**common_args)

# ─────────────────────── 5 Trainer & train ──────────────────────────
trainer = Trainer(
    model           = model,
    args            = args,
    train_dataset   = train_ds,
    eval_dataset    = val_ds,
    data_collator   = DataCollatorForLanguageModeling(tok, mlm=False),
    callbackss       = ([EarlyStoppingCallback(early_stopping_patience=2)]
                       if new_api else []),
)

print("🚀  fine-tuning…  (M1 Air: ~10 min for gpt2, ~25 min for gpt2-medium)")
trainer.train()

OUT_DIR.mkdir(parents=True, exist_ok=True)
trainer.save_model(OUT_DIR)
tok.save_pretrained(OUT_DIR)
print("✅  model saved →", OUT_DIR.resolve())