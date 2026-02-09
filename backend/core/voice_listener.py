import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import queue
import sys

class RealtimeTranscriber:
    # MODIFICATION 1: Accept a callback function in __init__
    def __init__(self, callback_function, model_size="base", device="cpu", compute_type="int8"):
        self.on_command_detected = callback_function  # Store the bridge to the server
        
        print(f"Loading Whisper model: {model_size}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Model loaded successfully!")
        
        # --- YOUR ORIGINAL PROMPT ---
        self.initial_prompt = (
            "Python programming keywords: and, character, characters,  as, assert, async, await, break, class, continue, "
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
            "secrets, io, queue, select, subprocess, concurrent, word, email, webbrowser, configparser."
        )
        
        # --- YOUR ORIGINAL AUDIO PARAMETERS ---
        self.sample_rate = 16000
        self.chunk_duration = 0.5 
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        self.min_silence_duration_ms = 1000 
        self.min_speech_duration_ms = 250 
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.speech_buffer = []
        self.silence_chunks = 0
        self.is_speaking = False
        
    def audio_callback(self, indata, frames, time, status):
        """Callback function to capture audio chunks."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        if self.is_recording:
            audio_data = indata[:, 0].astype(np.float32)
            self.audio_queue.put(audio_data.copy())
    
    def detect_speech(self, audio_chunk):
        """Detect if audio chunk contains speech using energy-based VAD."""
        rms_energy = np.sqrt(np.mean(audio_chunk ** 2))
        energy_threshold = 0.01 # Your original threshold
        return rms_energy > energy_threshold
    
    def transcribe_audio(self, audio_data):
        """Transcribe a chunk of audio."""
        try:
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",
                task="transcribe",
                vad_filter=False,
                initial_prompt=self.initial_prompt
            )
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text.strip())
            return " ".join(text_segments)
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    # MODIFICATION 2: Renamed to match Server expectation (optional, but cleaner)
    def start_transcription_loop(self):
        """Start real-time transcription."""
        print("\n" + "="*50)
        print("🎤 Real-time Transcription Started (Your Custom Code)")
        print("="*50 + "\n")
        
        self.is_recording = True
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=self.chunk_size,
            callback=self.audio_callback
        ):
            while self.is_recording:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.5)
                    has_speech = self.detect_speech(audio_chunk)
                    
                    if has_speech:
                        self.speech_buffer.append(audio_chunk)
                        self.silence_chunks = 0
                        if not self.is_speaking:
                            self.is_speaking = True
                            print("🎤 Speaking...", end="", flush=True)
                    else:
                        if self.is_speaking:
                            self.silence_chunks += 1
                            silence_duration = self.silence_chunks * self.chunk_duration
                            
                            if silence_duration >= (self.min_silence_duration_ms / 1000.0):
                                if len(self.speech_buffer) > 0:
                                    audio_data = np.concatenate(self.speech_buffer)
                                    speech_duration = len(audio_data) / self.sample_rate
                                    
                                    if speech_duration >= (self.min_speech_duration_ms / 1000.0):
                                        print() 
                                        transcription = self.transcribe_audio(audio_data)
                                        
                                        if transcription:
                                            # MODIFICATION 3: Send to Server instead of just printing
                                            print(f"📝 {transcription}")
                                            self.on_command_detected(transcription)
                                    
                                    self.speech_buffer = []
                                    self.is_speaking = False
                                    self.silence_chunks = 0
                except queue.Empty:
                    continue