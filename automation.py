# automation.py
import os
import pywhatkit
import webbrowser
import pyautogui
from speech_engine import speak
import subprocess

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

def shutdown_system():
    """Shuts down the Mac laptop - Multiple methods for reliability"""
    speak("Initiating system shutdown. Goodbye.")
    import time
    time.sleep(2)
    
    try:
        # Method 1: Direct shutdown command (most reliable)
        subprocess.call(['sudo', 'shutdown', '-h', 'now'])
    except:
        try:
            # Method 2: Using osascript without sudo
            os.system('osascript -e "tell application \\"System Events\\" to shut down"')
        except:
            try:
                # Method 3: Alternative shutdown
                os.system("shutdown -h now")
            except:
                speak("Unable to shutdown. Please shutdown manually.")

def restart_system():
    """Restarts the Mac laptop"""
    speak("Initiating system restart.")
    import time
    time.sleep(2)
    
    try:
        # Method 1: Direct restart
        subprocess.call(['sudo', 'shutdown', '-r', 'now'])
    except:
        try:
            # Method 2: Using osascript
            os.system('osascript -e "tell application \\"System Events\\" to restart"')
        except:
            try:
                # Method 3: Alternative restart
                os.system("shutdown -r now")
            except:
                speak("Unable to restart. Please restart manually.")

def sleep_system():
    """Puts the Mac to sleep"""
    speak("Putting system to sleep. Good night.")
    import time
    time.sleep(1)
    
    try:
        # pmset sleepnow is the most reliable for Mac
        os.system("pmset sleepnow")
    except:
        try:
            # Alternative method
            os.system('osascript -e "tell application \\"System Events\\" to sleep"')
        except:
            speak("Unable to sleep system.")