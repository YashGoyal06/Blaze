# automation.py
import os
import pywhatkit
import webbrowser
import pyautogui
import subprocess
import time

# NOTE: We removed 'from speech_engine import speak' from here to fix the crash.

def open_app(app_name):
    """Opens Mac applications"""
    from speech_engine import speak  # Local import to prevent circular crash
    try:
        os.system(f"open -a '{app_name}'")
        speak(f"Opening {app_name}")
    except Exception as e:
        speak(f"Could not open {app_name}")

def search_google(query):
    from speech_engine import speak
    speak(f"Searching Google for {query}")
    pywhatkit.search(query)

def play_youtube(video_name):
    from speech_engine import speak
    speak(f"Playing {video_name} on YouTube")
    pywhatkit.playonyt(video_name)

def minimize_window():
    pyautogui.hotkey('command', 'm')
    
def take_screenshot():
    from speech_engine import speak
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    speak("Screenshot saved.")

def shutdown_system():
    from speech_engine import speak
    speak("Initiating system shutdown. Goodbye.")
    time.sleep(2)
    try:
        subprocess.call(['sudo', 'shutdown', '-h', 'now'])
    except:
        os.system("shutdown -h now")

def restart_system():
    from speech_engine import speak
    speak("Initiating system restart.")
    time.sleep(2)
    try:
        subprocess.call(['sudo', 'shutdown', '-r', 'now'])
    except:
        os.system("shutdown -r now")

def sleep_system():
    from speech_engine import speak
    speak("Putting system to sleep. Good night.")
    time.sleep(1)
    try:
        os.system("pmset sleepnow")
    except:
        speak("Unable to sleep system.")