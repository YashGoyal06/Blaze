import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import threading
import cv2
import config
import speech_engine as io
import face_auth
import automation

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BlazeUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Config ---
        self.title("BLAZE PROTOCOL")
        self.geometry("900x600")
        self.resizable(False, False)
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Controls) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="BLAZE", font=("Orbitron", 30, "bold"), text_color="#00FFFF")
        self.logo_label.pack(pady=30)
        
        self.status_btn = ctk.CTkButton(self.sidebar, text="SYSTEM STATUS: IDLE", fg_color="#333333", hover=False)
        self.status_btn.pack(pady=10)

        self.mic_btn = ctk.CTkButton(self.sidebar, text="MIC: OFF", fg_color="#aa0000", height=40)
        self.mic_btn.pack(pady=10)

        # --- Main Area (Live Feed & Logs) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="black")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Camera Placeholder (The "Eye")
        self.cam_label = ctk.CTkLabel(self.main_frame, text="[ SENSOR OFFLINE ]", text_color="gray", font=("Courier", 16))
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Terminal Log (Bottom)
        self.log_box = ctk.CTkTextbox(self.main_frame, height=150, fg_color="#0f0f0f", text_color="#00ff00", font=("Consolas", 12))
        self.log_box.pack(fill="x", padx=10, pady=10)

        # Start Logic
        self.is_listening = False
        self.after(1000, self.boot_system)

    def log(self, message):
        self.log_box.insert("end", f"> {message}\n")
        self.log_box.see("end")

    def speak(self, text):
        # We run TTS in a thread so it doesn't freeze the UI
        threading.Thread(target=io.speak, args=(text,)).start()

    def display_frame(self, frame):
        """Converts CV2 frame to Image and displays it on the Label"""
        # Convert BGR (OpenCV) to RGB (Pillow)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize to fit UI
        frame = cv2.resize(frame, (640, 480)) 
        img = Image.fromarray(frame)
        imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
        self.cam_label.configure(image=imgtk, text="")
    
    def clear_camera_view(self):
        self.cam_label.configure(image=None, text="[ AUTHENTICATION CLOSED ]")

    # --- MAIN LOGIC FLOW ---

    def boot_system(self):
        self.log("SYSTEM BOOT INITIATED...")
        threading.Thread(target=self.run_auth_sequence, daemon=True).start()

    def run_auth_sequence(self):
        self.log("CHECKING BIOMETRIC DATABASE...")
        
        # Check if user needs to register
        if not face_auth.is_user_registered():
            self.log("NO USER FOUND. INITIATING REGISTRATION...")
            success = face_auth.capture_and_train(self)
            if not success:
                self.log("REGISTRATION FAILED.")
                return
        
        # Login Mode
        self.log("DATABASE FOUND. VERIFYING IDENTITY...")
        verified = face_auth.verify_user(self)
        
        if verified:
            self.status_btn.configure(text="SYSTEM STATUS: ONLINE", fg_color="#00aa00") # Green
            self.log("ACCESS GRANTED.")
            self.speak(f"Welcome back, {config.USER_NAME}. I am listening.")
            self.start_listening_loop()
        else:
            self.status_btn.configure(text="STATUS: BREACH", fg_color="#ff0000") # Red
            self.log("ACCESS DENIED. INTRUDER DETECTED.")
            self.speak("Face not recognized. System locking.")

    def start_listening_loop(self):
        self.is_listening = True
        self.mic_btn.configure(text="MIC: ACTIVE", fg_color="#00aa00")
        
        while self.is_listening:
            command = io.listen()
            
            if command == "none": continue
            
            self.log(f"CMD: {command}")
            
            # --- COMMANDS ---
            if "blaze" in command:
                if "open" in command:
                    app = command.replace("open", "").replace("blaze", "").strip()
                    automation.open_app(app)
                elif "search" in command:
                    q = command.replace("search", "").strip()
                    automation.search_google(q)
                elif "stop" in command:
                    self.speak("Goodbye.")
                    self.destroy()
                    break

if __name__ == "__main__":
    app = BlazeUI()
    app.mainloop()