import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import queue
import sys
import threading
from collections import deque

class RealtimeTranscriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):

        print(f"Loading Whisper model: {model_size}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Model loaded successfully!")
        
        # Python keywords and programming terms for better recognition (hot words)
        # This helps the model recognize technical terms when spoken
        self.initial_prompt = (
            "Python programming keywords: and, as, assert, async, await, break, class, continue, "
            "def, del, elif, else, except, False, finally, for, from, global, if, import, in, is, "
            "lambda, None, nonlocal, not, or, pass, raise, return, True, try, while, with, yield. "
            "Common programming terms: indent, indentation, statement, function, variable, method, "
            "parameter, argument, list, dictionary, tuple, set, string, integer, float, boolean, "
            "array, object, instance, module, package, library, syntax, error, exception, loop, "
            "iteration, condition, expression, operator, assignment, comparison, logical, arithmetic, "
            "slice, index, key, value, item, element, attribute, property, decorator, generator, "
            "iterator, comprehension, closure, recursion, algorithm, data structure, stack, queue, "
            "tree, graph, hash, sort, search, filter, map, reduce, enumerate, zip, range, len, "
            "type, isinstance, print, input, int, float, str, bool, append, extend, insert, remove, "
            "pop, clear, copy, count, reverse, sort, keys, values, items, get, update, split, "
            "join, strip, replace, find, lower, upper, title, format, f-string, switch, case, "
            "default, enum, dataclass, abstract, static, classmethod, staticmethod, property, super, "
            "self, init, new, del, repr, iter, next, call, add, sub, mul, div, mod, pow, xor, "
            "lt, le, eq, ne, gt, ge, contains, getattr, setattr, delattr, getattribute, "
            "defaultdict, Counter, OrderedDict, deque, namedtuple, collections, itertools, "
            "functools, operator, pickle, json, csv, os, sys, pathlib, datetime, time, random, "
            "math, statistics, re, string, threading, multiprocessing, asyncio, socket, http, "
            "urllib, html, xml, uuid, logging, argparse, shutil, tempfile, glob, fnmatch, hashlib, "
            "secrets, io, queue, select, subprocess, concurrent, email, webbrowser, configparser."
        )
        
        # Audio parameters
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.chunk_duration = 0.5  # Process 0.5 second chunks for VAD
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # VAD parameters
        self.min_silence_duration_ms = 1000  # 1 second of silence to end speech segment
        self.min_speech_duration_ms = 250  # Minimum speech duration to consider
        
        # Audio buffer
        self.audio_queue = queue.Queue()
        self.is_recording = False
        # Speech detection state
        self.speech_buffer = []  # Accumulates audio during speech
        self.silence_chunks = 0  # Counts consecutive silence chunks
        self.is_speaking = False
        
    def audio_callback(self, indata, frames, time, status):
        """Callback function to capture audio chunks."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        if self.is_recording:
            # Convert to float32 and add to queue
            audio_data = indata[:, 0].astype(np.float32)
            self.audio_queue.put(audio_data.copy())
    
    def detect_speech(self, audio_chunk):
        """Detect if audio chunk contains speech using energy-based VAD."""
        # Use energy-based detection for fast real-time VAD
        # Calculate RMS (Root Mean Square) energy
        rms_energy = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Threshold for speech detection (adjust if needed)
        # You can lower this if it's too sensitive, or raise if it picks up too much noise
        energy_threshold = 0.01
        
        return rms_energy > energy_threshold
    
    def transcribe_audio(self, audio_data):
        """Transcribe a chunk of audio."""
        try:
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",  # Change to None for auto-detection
                task="transcribe",
                vad_filter=False,  # We're already doing VAD manually
                initial_prompt=self.initial_prompt  # Hot words for Python keywords and programming terms
            )
            
            # Get the transcribed text
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text.strip())
            
            return " ".join(text_segments)
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    def start_transcription(self):
        """Start real-time transcription."""
        print("\n" + "="*50)
        print("Real-time Transcription Started")
        print("Listening for speech... (will transcribe when you stop speaking)")
        print("Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        self.is_recording = True
        
        try:
            # Start audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=self.audio_callback
            ):
                while self.is_recording:
                    try:
                        # Get audio chunk from queue (with timeout)
                        audio_chunk = self.audio_queue.get(timeout=0.5)
                        
                        # Detect if this chunk contains speech
                        has_speech = self.detect_speech(audio_chunk)
                        
                        if has_speech:
                            # Speech detected - add to buffer
                            self.speech_buffer.append(audio_chunk)
                            self.silence_chunks = 0
                            
                            if not self.is_speaking:
                                self.is_speaking = True
                                print("🎤 Speaking...", end="", flush=True)
                        else:
                            # Silence detected
                            if self.is_speaking:
                                # We were speaking, count silence chunks
                                self.silence_chunks += 1
                                
                                # If we've had enough silence, transcribe the accumulated speech
                                silence_duration = self.silence_chunks * self.chunk_duration
                                if silence_duration >= (self.min_silence_duration_ms / 1000.0):
                                    # Transcribe the accumulated speech (only speech chunks, no silence)
                                    if len(self.speech_buffer) > 0:
                                        audio_data = np.concatenate(self.speech_buffer)
                                        
                                        # Check minimum speech duration
                                        speech_duration = len(audio_data) / self.sample_rate
                                        if speech_duration >= (self.min_speech_duration_ms / 1000.0):
                                            print()  # New line after "Speaking..."
                                            transcription = self.transcribe_audio(audio_data)
                                            
                                            if transcription:
                                                print(f"📝 {transcription}\n")
                                        
                                        # Clear the buffer
                                        self.speech_buffer = []
                                        self.is_speaking = False
                                        self.silence_chunks = 0
                            # If not speaking, just ignore silence (do nothing)
                            
                    except queue.Empty:
                        continue
                    except KeyboardInterrupt:
                        break
                        
        except KeyboardInterrupt:
            print("\nStopping transcription...")
        finally:
            self.is_recording = False
            print("Transcription stopped.")

def main():
    """Main function to run the transcriber."""
    # Configuration
    MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large-v2, large-v3
    DEVICE = "cpu"  # Use "cuda" if you have GPU support
    COMPUTE_TYPE = "int8"  # Options: int8, int8_float16, float16, float32
    
    # For GPU, you might want to use:
    # DEVICE = "cuda"
    # COMPUTE_TYPE = "float16"
    
    # Create and start transcriber
    transcriber = RealtimeTranscriber(
        model_size=MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE
    )
    
    transcriber.start_transcription()

if __name__ == "__main__":
    main()
