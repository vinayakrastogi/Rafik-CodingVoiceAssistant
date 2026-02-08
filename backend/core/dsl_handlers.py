import re
# Optional: from word2number import w2n

# --- THE REGISTRY ---
# This dictionary will be automatically populated
HANDLER_REGISTRY = {}

def register_handler(intent_name):
    """Decorator to register a function to an intent."""
    def decorator(func):
        HANDLER_REGISTRY[intent_name] = func
        return func
    return decorator

# --- HELPER FUNCTIONS ---
def extract_number(text, default=1):
    numbers = re.findall(r'\b\d+\b', text)
    return numbers[0] if numbers else str(default)

def extract_direction(text, default="down"):
    text = text.lower()
    if any(x in text for x in ["up", "previous", "back"]): return "up"
    if any(x in text for x in ["down", "next", "forward"]): return "down"
    if "left" in text: return "left"
    if "right" in text: return "right"
    return default

# --- YOUR HANDLERS (Just add @register_handler) ---

@register_handler("MOVE_CURSOR")
def handle_move(text):
    qty = extract_number(text, 1)
    direction = extract_direction(text, "down")
    
    unit = "line"
    if "word" in text: unit = "word"
    elif "char" in text: unit = "char"
    
    return f"MOVE_CURSOR({unit}, {qty}, {direction})"

@register_handler("JUMP_TO_LINE")
def handle_jump_line(text):
    qty = extract_number(text, 1)
    return f"JUMP_TO_LINE({qty})"

@register_handler("JUMP_TO_SCOPE")
def handle_jump_scope(text):
    scope = "function"
    if "class" in text: scope = "class"
    
    direction = extract_direction(text, "down")
    return f"JUMP_TO_SCOPE({scope}, {direction})"

@register_handler("JUMP_TO_DEFINITION")
def handle_jump_def(text):
    # Logic to extract the last word as the target
    words = text.split()
    ignore = ["jump", "to", "definition", "of", "the"]
    target = words[-1] if words else "unknown"
    return f"JUMP_TO_DEFINITION({target})"

@register_handler("SCROLL")
def handle_scroll(text):
    qty = extract_number(text, 1)
    direction = extract_direction(text, "down")
    return f"SCROLL({direction}, {qty})"