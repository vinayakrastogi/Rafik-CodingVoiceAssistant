import threading
import re
import uvicorn
from fastapi import FastAPI
from core.inference_engine import RafikParser
from core.voice_listener import RealtimeTranscriber

app = FastAPI()

# 1. Initialize Brain
bot = RafikParser()

# 2. Global Command Queue
current_command = {"type": "EMPTY"}

def parse_dsl_to_json(dsl_string):
    try:
        if "ERROR" in dsl_string or "NO_HANDLER" in dsl_string:
            return None
        
        command_type = dsl_string.split('(')[0]
        content = re.search(r'\((.*?)\)', dsl_string)
        params = [p.strip() for p in content.group(1).split(',')] if content else []
            
        return {"type": command_type, "params": params}
    except Exception as e:
        print(f"DSL Error: {e}")
        return None

# 3. Define what happens when Voice hears something
def on_voice_command(text):
    global current_command
    
    # A. Predict Intent (Brain)
    dsl, intent = bot.predict(text)
    print(f"🤖 DSL Generated: {dsl}")
    
    # B. Convert to JSON
    cmd_json = parse_dsl_to_json(dsl)
    
    # C. Queue for VS Code
    if cmd_json:
        current_command = cmd_json
        print(f"📨 Queued for Client: {cmd_json['type']}")

# 4. API Endpoint for VS Code
@app.get("/fetch_command")
def fetch_command():
    global current_command
    if current_command["type"] != "EMPTY":
        cmd = current_command
        current_command = {"type": "EMPTY"}
        return cmd
    return {"type": "EMPTY"}

if __name__ == "__main__":
    # Start Voice in Background Thread
    # We pass 'on_voice_command' so the listener knows where to send text
    transcriber = RealtimeTranscriber(callback_function=on_voice_command)
    voice_thread = threading.Thread(target=transcriber.start_transcription_loop, daemon=True)
    voice_thread.start()
    
    # Start API Server
    print("🚀 Rafik Backend Initialized on Port 8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")