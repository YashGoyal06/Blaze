# speech_engine.py
import pyttsx3
import speech_recognition as sr
import config

# Initialize TTS Engine
engine = pyttsx3.init()
# Mac voices: usually index 0 is system default, 1 is often a female voice, etc.
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) 
engine.setProperty('rate', 190) # Speed of speech

def speak(text):
    """Converts text to speech"""
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