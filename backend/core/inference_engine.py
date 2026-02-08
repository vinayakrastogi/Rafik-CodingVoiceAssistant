import torch
import os
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast
from . import dsl_handlers 

class RafikParser:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # FIX PATH: Point to the new 'models' folder
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_path, "models", "intent_router_model")
        
        print(f"Loading Router from {model_path}...")
        
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
        self.id2label = self.model.config.id2label
        
        # Load Handlers
        self.handlers = dsl_handlers.HANDLER_REGISTRY
        print(f"✅ Loaded {len(self.handlers)} command handlers")

    def predict(self, text):
        # (Keep the rest of your predict function exactly the same)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        
        pred_id = torch.argmax(logits, dim=1).item()
        intent = self.id2label[pred_id]
        
        if intent in self.handlers:
            try:
                dsl = self.handlers[intent](text)
                return dsl, intent
            except Exception as e:
                return f"ERROR_IN_HANDLER: {str(e)}", intent
        else:
            return f"NO_HANDLER_FOR: {intent}", intent
# --- Main Loop ---
if __name__ == "__main__":
    bot = RafikParser()
    print("\n--- Rafik Modular AI (Type 'exit') ---")
    
    while True:
        cmd = input("\nCommand: ")
        if cmd.lower() in ["exit", "quit"]: break
        
        dsl, intent = bot.predict(cmd)
        print(f" -> Intent: {intent}")
        print(f" -> DSL:    {dsl}")