import json
import os  # <--- NEW IMPORT
import torch
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)

# --- PATH CONFIGURATION (THE FIX) ---
# 1. Get the folder where this script lives (backend/training)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Get the backend folder (one level up)
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)

# 3. Define correct absolute paths
DATA_FILE = os.path.join(SCRIPT_DIR, "commands.json")  # Assumes json is inside training/
MODEL_OUTPUT = os.path.join(BACKEND_DIR, "models", "intent_router_model") # Targets backend/models/

print(f"📂 Data Source: {DATA_FILE}")
print(f"💾 Model Target: {MODEL_OUTPUT}")

# --- REST OF YOUR CODE (Unchanged) ---
# ...

# 1. Load Data & Flatten
# We only care about Text -> Label (Intent)
def load_and_flatten():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    texts = []
    labels = []
    
    # We collect all intents found in the JSON keys
    intent_names = list(data.keys())
    # Create a mapping: "MOVE_CURSOR" -> 0, "SCROLL" -> 1
    label2id = {name: i for i, name in enumerate(intent_names)}
    id2label = {i: name for i, name in enumerate(intent_names)}
    
    for intent, items in data.items():
        for item in items:
            texts.append(item['text'])
            labels.append(label2id[intent])
            
    return texts, labels, label2id, id2label

texts, labels, label2id, id2label = load_and_flatten()

# 2. Prepare Dataset
dataset = Dataset.from_dict({"text": texts, "label": labels})
dataset = dataset.train_test_split(test_size=0.1)

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True, padding=True)

tokenized_datasets = dataset.map(preprocess_function, batched=True)

# 3. Train the Router
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", 
    num_labels=len(label2id),
    id2label=id2label,
    label2id=label2id
)

args = TrainingArguments(
    output_dir=MODEL_OUTPUT,
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    num_train_epochs=10, # Fast training for intent
    weight_decay=0.01,
    save_strategy="epoch",
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    # tokenizer=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
)

print("🚀 Training Intent Router...")
trainer.train()

trainer.save_model(MODEL_OUTPUT)
print("✅ Router Saved!")