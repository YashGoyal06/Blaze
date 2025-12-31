# speech_engine.py
import pyttsx3
import speech_recognition as sr
import config

# Initialize TTS Engine
engine = pyttsx3.init()

# Get available voices
voices = engine.getProperty('voices')

# Try to find a male voice
male_voice = None
for voice in voices:
    # On Mac, male voices often have these indicators
    if 'male' in voice.name.lower() or 'daniel' in voice.name.lower() or 'alex' in voice.name.lower():
        male_voice = voice.id
        break

# If no specific male voice found, use first available (usually male on Mac)
if male_voice:
    engine.setProperty('voice', male_voice)
else:
    # Fallback to first voice
    engine.setProperty('voice', voices[0].id)

# Voice properties for deeper, more masculine sound
engine.setProperty('rate', 175)      # Slower speech = deeper perception
engine.setProperty('volume', 1.0)    # Max volume for authority
# Note: Pitch adjustment not supported on Mac NSSS, so we skip it

def speak(text):
    """Converts text to speech with masculine voice"""
    print(f"{config.ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listens to microphone and returns text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            print(f"You: {command}")
            return command.lower()
        except sr.WaitTimeoutError:
            return "none"
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            speak("Network error.")
            return "none"

def list_available_voices():
    """Helper function to see all available voices on your system"""
    print("\n=== Available Voices ===")
    for idx, voice in enumerate(voices):
        print(f"{idx}: {voice.name} - {voice.id}")
        print(f"   Languages: {voice.languages}")
        print(f"   Gender: {voice.gender if hasattr(voice, 'gender') else 'Unknown'}")
        print()

# Uncomment this line to see all available voices on your Mac
# list_available_voices()