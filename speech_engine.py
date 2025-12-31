import asyncio
import edge_tts
import os
import speech_recognition as sr
import config
import threading
import hashlib

# --- CONFIGURATION: MALE VOICE ---
VOICE = "en-US-ChristopherNeural" 

# --- CACHE SETUP ---
CACHE_DIR = "voice_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# --- 1. Global Microphone Initialization ---
recognizer = sr.Recognizer()
mic = sr.Microphone()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 400

try:
    with mic as source:
        print("Calibrating background noise... (One time)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
except Exception as e:
    print(f"Microphone error: {e}")

# --- 2. Caching & Audio Logic ---
def get_cache_path(text):
    """Creates a unique filename for each phrase based on its text"""
    hash_obj = hashlib.md5(text.encode())
    return os.path.join(CACHE_DIR, f"{hash_obj.hexdigest()}.mp3")

async def _generate_audio(text, output_file):
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_file)
        return True
    except Exception as e:
        print(f"TTS Gen Error: {e}")
        return False

def _run_speak_thread(text):
    file_path = get_cache_path(text)
    
    # 1. Check if we already have this audio cached
    if os.path.exists(file_path):
        os.system(f"afplay '{file_path}'")
        return

    # 2. If not, generate it
    try:
        success = asyncio.run(_generate_audio(text, file_path))
        
        # 3. Play it
        if success and os.path.exists(file_path):
            os.system(f"afplay '{file_path}'")
            # We DO NOT delete the file anymore. We keep it for speed next time.
    except Exception as e:
        print(f"Playback Error: {e}")

def prefetch(text):
    """Generates audio in background WITHOUT playing it (for speed)"""
    file_path = get_cache_path(text)
    if not os.path.exists(file_path):
        threading.Thread(target=lambda: asyncio.run(_generate_audio(text, file_path)), daemon=True).start()

def speak(text):
    """Plays audio (Instant if cached, otherwise generates)"""
    print(f"{config.ASSISTANT_NAME}: {text}")
    threading.Thread(target=_run_speak_thread, args=(text,), daemon=True).start()

def listen():
    with mic as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            command = recognizer.recognize_google(audio)
            print(f"You: {command}")
            return command.lower()
        except sr.WaitTimeoutError:
            return "none"
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            return "none"
        except Exception as e:
            print(f"Error: {e}")
            return "none"