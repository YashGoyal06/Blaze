import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import threading
import cv2
import config
import speech_engine as io
import face_auth
import automation
import math
import time
import numpy as np

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BlazeUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Config ---
        self.title("BLAZE AI")
        self.geometry("1200x800")
        self.resizable(False, False)
        self.configure(fg_color="#0a0a0f")
        
        # Animation variables
        self.animation_angle = 0
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self.scanning_line = 0
        self.voice_amplitude = []
        self.is_speaking = False
        
        # State management
        self.current_state = "boot"  # boot, verifying, authenticated, listening
        self.is_listening = False
        
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Create canvas for animations
        self.canvas = tk.Canvas(
            self.main_container,
            bg="#0a0a0f",
            highlightthickness=0,
            width=1200,
            height=800
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Initialize UI elements
        self.setup_boot_screen()
        
        # Start animation loop
        self.animate()
        
        # Start system after 2 seconds
        self.after(2000, self.boot_system)

    def setup_boot_screen(self):
        """Initial boot screen with BLAZE logo"""
        self.canvas.delete("all")
        
        # Draw central circle
        cx, cy = 600, 400
        
        # Outer glow circles
        for i in range(5):
            r = 150 + i * 20
            alpha = 50 - i * 10
            color = f"#{int(0):02x}{int(150-i*20):02x}{int(255-i*30):02x}"
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=color, width=2, tags="boot_glow"
            )
        
        # Central text
        self.canvas.create_text(
            cx, cy - 50,
            text="BLAZE",
            font=("Orbitron", 60, "bold"),
            fill="#00ffff",
            tags="boot_text"
        )
        
        self.canvas.create_text(
            cx, cy + 30,
            text="ARTIFICIAL INTELLIGENCE SYSTEM",
            font=("Orbitron", 14),
            fill="#00aaff",
            tags="boot_text"
        )
        
        self.canvas.create_text(
            cx, cy + 80,
            text="Initializing...",
            font=("Consolas", 12),
            fill="#00ff88",
            tags="boot_status"
        )

    def setup_verification_screen(self):
        """Face verification screen with scanning animation"""
        self.canvas.delete("all")
        self.current_state = "verifying"
        
        cx, cy = 600, 400
        
        # Title
        self.canvas.create_text(
            600, 80,
            text="BIOMETRIC VERIFICATION",
            font=("Orbitron", 32, "bold"),
            fill="#00ffff",
            tags="verify_title"
        )
        
        # Camera feed area (will be updated with actual frame)
        self.canvas.create_rectangle(
            350, 150, 850, 550,
            outline="#00ffff",
            width=2,
            tags="camera_border"
        )
        
        # Corner brackets
        bracket_size = 30
        corners = [
            (350, 150), (850, 150),  # Top corners
            (350, 550), (850, 550)   # Bottom corners
        ]
        
        for i, (x, y) in enumerate(corners):
            if i == 0:  # Top-left
                self.canvas.create_line(x, y, x + bracket_size, y, fill="#00ffff", width=3, tags="brackets")
                self.canvas.create_line(x, y, x, y + bracket_size, fill="#00ffff", width=3, tags="brackets")
            elif i == 1:  # Top-right
                self.canvas.create_line(x, y, x - bracket_size, y, fill="#00ffff", width=3, tags="brackets")
                self.canvas.create_line(x, y, x, y + bracket_size, fill="#00ffff", width=3, tags="brackets")
            elif i == 2:  # Bottom-left
                self.canvas.create_line(x, y, x + bracket_size, y, fill="#00ffff", width=3, tags="brackets")
                self.canvas.create_line(x, y, x, y - bracket_size, fill="#00ffff", width=3, tags="brackets")
            else:  # Bottom-right
                self.canvas.create_line(x, y, x - bracket_size, y, fill="#00ffff", width=3, tags="brackets")
                self.canvas.create_line(x, y, x, y - bracket_size, fill="#00ffff", width=3, tags="brackets")
        
        # Status text
        self.canvas.create_text(
            600, 600,
            text="Scanning facial features...",
            font=("Consolas", 14),
            fill="#00ff88",
            tags="verify_status"
        )
        
        # Progress indicator
        self.canvas.create_rectangle(
            400, 650, 800, 670,
            outline="#00ffff",
            width=2,
            tags="progress_border"
        )
        
        self.canvas.create_rectangle(
            400, 650, 400, 670,
            fill="#00ffff",
            outline="",
            tags="progress_fill"
        )

    def setup_voice_assistant_screen(self):
        """Modern voice assistant interface"""
        self.canvas.delete("all")
        self.current_state = "authenticated"
        
        cx, cy = 600, 400
        
        # Title
        self.canvas.create_text(
            600, 80,
            text="BLAZE AI ASSISTANT",
            font=("Orbitron", 32, "bold"),
            fill="#00ffff",
            tags="assistant_title"
        )
        
        # Central orb area
        self.orb_radius = 120
        
        # Create multiple circles for the orb effect
        for i in range(6):
            r = self.orb_radius + i * 15
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=f"#00{int(150-i*20):02x}ff",
                width=1,
                tags=f"orb_ring_{i}"
            )
        
        # Central glow
        self.canvas.create_oval(
            cx - self.orb_radius, cy - self.orb_radius,
            cx + self.orb_radius, cy + self.orb_radius,
            fill="#001a33",
            outline="#00ffff",
            width=3,
            tags="orb_center"
        )
        
        # Status text
        self.canvas.create_text(
            600, 600,
            text="Listening...",
            font=("Orbitron", 18),
            fill="#00ff88",
            tags="assistant_status"
        )
        
        # Command display area
        self.canvas.create_rectangle(
            200, 650, 1000, 750,
            fill="#0f0f1a",
            outline="#00ffff",
            width=2,
            tags="command_box"
        )
        
        self.canvas.create_text(
            600, 700,
            text="Say 'Blaze' to give a command",
            font=("Consolas", 14),
            fill="#00aaff",
            tags="command_text"
        )

    def update_camera_feed(self, frame):
        """Update camera feed during verification"""
        if self.current_state != "verifying":
            return
            
        # Resize frame to fit
        frame = cv2.resize(frame, (500, 400))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        img = Image.fromarray(frame)
        
        # Create photo image
        self.camera_photo = ImageTk.PhotoImage(img)
        
        # Update canvas
        self.canvas.delete("camera_feed")
        self.canvas.create_image(
            600, 350,
            image=self.camera_photo,
            tags="camera_feed"
        )
        
        # Keep camera border on top
        self.canvas.tag_raise("camera_border")
        self.canvas.tag_raise("brackets")

    def update_verification_progress(self, progress):
        """Update progress bar during verification"""
        width = 400 * (progress / 100)
        self.canvas.coords("progress_fill", 400, 650, 400 + width, 670)

    def update_verification_status(self, text):
        """Update status text during verification"""
        self.canvas.itemconfig("verify_status", text=text)

    def update_command_text(self, text):
        """Update command text in assistant mode"""
        if self.current_state == "authenticated":
            self.canvas.itemconfig("command_text", text=text)

    def animate(self):
        """Main animation loop"""
        self.animation_angle += 2
        if self.animation_angle >= 360:
            self.animation_angle = 0
        
        # Pulse effect
        self.pulse_alpha += self.pulse_direction * 5
        if self.pulse_alpha >= 100 or self.pulse_alpha <= 0:
            self.pulse_direction *= -1
        
        if self.current_state == "boot":
            self.animate_boot()
        elif self.current_state == "verifying":
            self.animate_verification()
        elif self.current_state == "authenticated":
            self.animate_assistant()
        
        # Continue animation
        self.after(30, self.animate)

    def animate_boot(self):
        """Animate boot screen"""
        try:
            # Rotate glow circles
            cx, cy = 600, 400
            angle_rad = math.radians(self.animation_angle)
            
            # Update glow circles
            items = self.canvas.find_withtag("boot_glow")
            for i, item in enumerate(items):
                offset = i * 72  # 360/5
                current_angle = self.animation_angle + offset
                alpha_val = int(50 + 30 * math.sin(math.radians(current_angle)))
                
        except:
            pass

    def animate_verification(self):
        """Animate verification screen"""
        try:
            # Animate scanning line
            self.scanning_line += 5
            if self.scanning_line > 400:
                self.scanning_line = 0
            
            # Draw scanning line
            self.canvas.delete("scan_line")
            y = 150 + self.scanning_line
            self.canvas.create_line(
                350, y, 850, y,
                fill="#00ff88",
                width=2,
                tags="scan_line"
            )
            
            # Pulse brackets
            alpha = int(255 * (self.pulse_alpha / 100))
            
        except:
            pass

    def animate_assistant(self):
        """Animate voice assistant orb"""
        try:
            cx, cy = 600, 400
            
            # Rotate rings
            for i in range(6):
                tag = f"orb_ring_{i}"
                items = self.canvas.find_withtag(tag)
                if items:
                    angle_offset = i * 60
                    current_angle = self.animation_angle + angle_offset
                    
                    # Create pulsing effect
                    scale = 1 + 0.1 * math.sin(math.radians(current_angle))
                    r = (self.orb_radius + i * 15) * scale
                    
                    self.canvas.coords(
                        items[0],
                        cx - r, cy - r, cx + r, cy + r
                    )
            
            # Pulse center orb
            scale = 1 + 0.05 * math.sin(math.radians(self.animation_angle * 2))
            r = self.orb_radius * scale
            self.canvas.coords(
                "orb_center",
                cx - r, cy - r, cx + r, cy + r
            )
            
            # Add particle effects when listening
            if self.is_listening and self.animation_angle % 10 == 0:
                self.add_particle_effect(cx, cy)
                
        except:
            pass

    def add_particle_effect(self, cx, cy):
        """Add particle effects around orb"""
        angle = math.radians(self.animation_angle + np.random.randint(0, 360))
        distance = self.orb_radius + 50
        
        x = cx + distance * math.cos(angle)
        y = cy + distance * math.sin(angle)
        
        particle = self.canvas.create_oval(
            x - 3, y - 3, x + 3, y + 3,
            fill="#00ffff",
            outline=""
        )
        
        # Fade out particle
        self.fade_particle(particle, 10)

    def fade_particle(self, particle, steps):
        """Fade out particle effect"""
        if steps > 0:
            self.after(30, lambda: self.fade_particle(particle, steps - 1))
        else:
            try:
                self.canvas.delete(particle)
            except:
                pass

    def speak(self, text):
        """Speak with visual feedback"""
        self.is_speaking = True
        threading.Thread(target=self._speak_thread, args=(text,)).start()

    def _speak_thread(self, text):
        """TTS in separate thread"""
        io.speak(text)
        self.is_speaking = False

    # --- MAIN LOGIC FLOW ---

    def boot_system(self):
        """Start the boot sequence"""
        threading.Thread(target=self.run_auth_sequence, daemon=True).start()

    def run_auth_sequence(self):
        """Run authentication sequence"""
        time.sleep(1)
        
        # Switch to verification screen
        self.after(0, self.setup_verification_screen)
        time.sleep(0.5)
        
        # Check if user needs to register
        if not face_auth.is_user_registered():
            self.after(0, lambda: self.update_verification_status("No user found. Initiating registration..."))
            success = face_auth.capture_and_train_animated(self)
            if not success:
                self.after(0, lambda: self.update_verification_status("Registration failed."))
                return
        
        # Login Mode
        self.after(0, lambda: self.update_verification_status("Verifying identity..."))
        verified = face_auth.verify_user_animated(self)
        
        if verified:
            self.after(0, lambda: self.update_verification_status("Access granted. Welcome back."))
            time.sleep(1)
            self.after(0, self.setup_voice_assistant_screen)
            self.speak(f"Welcome back, {config.USER_NAME}. I am listening.")
            time.sleep(2)
            self.start_listening_loop()
        else:
            self.after(0, lambda: self.update_verification_status("Access denied. Face not recognized."))
            self.speak("Face not recognized. System locking.")

    def start_listening_loop(self):
        """Start listening for commands"""
        self.is_listening = True
        
        def listen_thread():
            while self.is_listening:
                self.after(0, lambda: self.update_command_text("Listening..."))
                command = io.listen()
                
                if command == "none":
                    continue
                
                self.after(0, lambda c=command: self.update_command_text(f"You said: {c}"))
                
                # Process commands
                if "blaze" in command:
                    if "shutdown" in command or "shut down" in command:
                        self.speak("Shutting down the system. Goodbye.")
                        time.sleep(2)
                        automation.shutdown_system()
                        self.after(0, self.destroy)
                        break
                    elif "restart" in command or "reboot" in command:
                        automation.restart_system()
                        self.after(0, self.destroy)
                        break
                    elif "sleep" in command:
                        automation.sleep_system()
                        self.after(0, self.destroy)
                        break
                    elif "open" in command:
                        app = command.replace("open", "").replace("blaze", "").strip()
                        automation.open_app(app)
                    elif "search" in command:
                        q = command.replace("search", "").replace("blaze", "").strip()
                        automation.search_google(q)
                    elif "screenshot" in command:
                        automation.take_screenshot()
                    elif "stop" in command or "exit" in command:
                        self.speak("Goodbye.")
                        self.after(0, self.destroy)
                        break
                
                time.sleep(0.5)
        
        threading.Thread(target=listen_thread, daemon=True).start()


if __name__ == "__main__":
    app = BlazeUI()
    app.mainloop()