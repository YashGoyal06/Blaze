# automation.py
import os
import pywhatkit
import webbrowser
import pyautogui
from speech_engine import speak

def open_app(app_name):
    """Opens Mac applications"""
    try:
        # On MacOS, we use the 'open -a' command
        os.system(f"open -a '{app_name}'")
        speak(f"Opening {app_name}")
    except Exception as e:
        speak(f"Could not open {app_name}")

def search_google(query):
    speak(f"Searching Google for {query}")
    pywhatkit.search(query)

def play_youtube(video_name):
    speak(f"Playing {video_name} on YouTube")
    pywhatkit.playonyt(video_name)

def minimize_window():
    # Mac shortcut to minimize app (Cmd + M)
    pyautogui.hotkey('command', 'm')
    
def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    speak("Screenshot saved.")