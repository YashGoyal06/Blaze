import sys
import os
import random
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QGraphicsDropShadowEffect, 
                             QProgressBar, QFrame, QScrollArea)
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                          QPoint, QPointF, pyqtSignal, QThread, QObject, QRectF, QTime, QDate)
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QRadialGradient, 
                        QPainterPath, QFont, QLinearGradient, QImage)
import math
import time
import datetime
import subprocess

# Local imports
import config
import speech_engine as io
import face_auth
import automation

# Optional dependency for system stats
try:
    import psutil
except ImportError:
    psutil = None

# --- 1. SIGNAL BRIDGE ---
class FaceAuthSignals(QObject):
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(str)
    auth_result = pyqtSignal(bool)
    cam_update = pyqtSignal(QImage)

    def update_status(self, text):
        self.status_changed.emit(text)

    def update_progress(self, text):
        self.progress_changed.emit(text)

    def update_camera_frame(self, frame):
        try:
            h, w, ch = frame.shape
            target_size = 400
            scale = max(target_size / w, target_size / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            resized_frame = cv2.resize(frame, (new_w, new_h))
            rgb_image = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = ch * new_w
            
            qt_image = QImage(rgb_image.data, new_w, new_h, bytes_per_line, QImage.Format.Format_RGB888)
            self.cam_update.emit(qt_image.copy())
        except Exception:
            pass

class FaceAuthThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def run(self):
        time.sleep(0.5) 
        try:
            if not face_auth.is_user_registered():
                self.signals.update_status("UNKNOWN ENTITY")
                self.signals.update_progress("ALIGN FACE FOR CAPTURE")
                io.speak("Identity not found. Starting registration.")
                success = face_auth.capture_and_train_qt(self.signals)
                if success:
                    self.signals.update_status("REGISTRATION COMPLETE")
                    io.speak("Registration successful.")
                    self.signals.auth_result.emit(True)
                else:
                    self.signals.update_status("REGISTRATION FAILED")
                    self.signals.auth_result.emit(False)
                return

            self.signals.update_status("BIOMETRIC SCAN")
            self.signals.update_progress("Scanning...") 
            io.speak("Scanning biometric data")
            
            verified = face_auth.verify_user_qt(self.signals)
            self.signals.auth_result.emit(verified)

        except Exception as e:
            print(f"Error: {e}")
            self.signals.update_status("SYSTEM ERROR")
            self.signals.auth_result.emit(False)


class VoiceThread(QThread):
    command_received = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            command = io.listen()
            if self.running and command != "none":
                self.command_received.emit(command)
            time.sleep(0.1)
    
    def stop(self):
        self.running = False


# --- 2. NEW WIDGETS ---

class HUDClock(QWidget):
    """Displays Date and Time in a futuristic format"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 80)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Time
        current_time = QTime.currentTime().toString("HH:mm")
        painter.setPen(QPen(QColor(90, 180, 255), 1))
        painter.setFont(QFont("Helvetica", 32, QFont.Weight.Bold))
        painter.drawText(0, 40, current_time)
        
        # Date
        current_date = QDate.currentDate().toString("ddd, MMM d")
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Helvetica", 12))
        painter.drawText(2, 60, current_date.upper())

class SystemMonitor(QWidget):
    """Circular Progress Bars for CPU and RAM"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        self.cpu_usage = 0
        self.ram_usage = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def update_stats(self):
        if psutil:
            self.cpu_usage = psutil.cpu_percent()
            self.ram_usage = psutil.virtual_memory().percent
        else:
            self.cpu_usage = random.randint(10, 30) # Mock data if library missing
            self.ram_usage = random.randint(40, 60)
        self.update()

    def draw_circle_bar(self, painter, x, y, value, label):
        radius = 30
        
        # Background track
        painter.setPen(QPen(QColor(50, 50, 70), 4))
        painter.drawEllipse(x, y, radius*2, radius*2)
        
        # Value arc
        color = QColor(0, 255, 150) if value < 80 else QColor(255, 50, 50)
        painter.setPen(QPen(color, 4))
        span_angle = int(-value * 3.6 * 16)
        painter.drawArc(x, y, radius*2, radius*2, 90 * 16, span_angle)
        
        # Text
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Helvetica", 9))
        text_rect = QRectF(x, y + radius - 10, radius*2, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{int(value)}%")
        
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setFont(QFont("Helvetica", 8))
        label_rect = QRectF(x, y + radius * 2 + 5, radius*2, 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw_circle_bar(painter, 10, 10, self.cpu_usage, "CPU")
        self.draw_circle_bar(painter, 100, 10, self.ram_usage, "RAM")


# --- 3. ANIMATIONS ---
class BootSequenceWidget(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.frame_count = 0
        self.max_frames = 90
        self.opacity = 0
        self.ring_scale = 0.0
        self.loading_text = ""
        self.hex_codes = []
        
        self.timer.start(30)
        try:
            os.system("afplay /System/Library/Sounds/Glass.aiff &")
        except:
            pass

    def animate(self):
        self.frame_count += 1
        if self.frame_count < 40:
            self.ring_scale = min(1.0, self.frame_count / 30.0)
            self.opacity = min(255, self.frame_count * 10)
            if self.frame_count % 5 == 0:
                self.hex_codes = [f"0x{random.randint(0, 255):02X}" for _ in range(4)]
        elif self.frame_count < 70:
            self.loading_text = "INITIALIZING CORE SYSTEMS..."
        else:
            self.loading_text = "SYSTEM ONLINE"
            if self.frame_count >= self.max_frames:
                self.timer.stop()
                self.finished.emit()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        cyan = QColor(0, 255, 255, self.opacity)
        dark_cyan = QColor(0, 100, 100, self.opacity)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(cyan, 3))
        r1 = 150 * self.ring_scale
        painter.drawEllipse(QPointF(cx, cy), r1, r1)
        
        painter.setPen(QPen(dark_cyan, 5))
        r2 = 180 * self.ring_scale
        angle = (self.frame_count * 5) % 360
        painter.drawArc(int(cx-r2), int(cy-r2), int(r2*2), int(r2*2), angle * 16, 120 * 16)
        painter.drawArc(int(cx-r2), int(cy-r2), int(r2*2), int(r2*2), (angle + 180) * 16, 120 * 16)
        
        painter.setPen(QPen(QColor(255, 255, 255, self.opacity), 1))
        painter.setFont(QFont("Monaco", 12))
        if self.hex_codes:
            for i, code in enumerate(self.hex_codes):
                painter.drawText(int(cx + 200), int(cy - 40 + i*20), code)
                painter.drawText(int(cx - 250), int(cy - 40 + i*20), code)

        painter.setFont(QFont("Helvetica", 14, QFont.Weight.Bold))
        text_rect = QRectF(0, cy + 200, w, 50)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.loading_text)


class SiriOrb(QWidget):
    """Arc Reactor Style Assistant"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.pulse = 0
        self.state = "idle"
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(24)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 500)
    
    def set_state(self, state):
        self.state = state
    
    def animate(self):
        speed = 2 if self.state == "listening" else 0.5
        self.angle = (self.angle + speed) % 360
        self.pulse = (math.sin(time.time() * 5) + 1) / 2 if self.state == "speaking" else 0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 250, 250
        cyan = QColor(0, 255, 255)
        
        painter.setPen(QPen(cyan, 8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 100, 100)
        
        painter.setPen(Qt.PenStyle.NoPen)
        glow = QRadialGradient(cx, cy, 90)
        glow.setColorAt(0, QColor(0, 255, 255, 100))
        glow.setColorAt(1, Qt.GlobalColor.transparent)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPointF(cx, cy), 90, 90)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 4))
        for i in range(3):
            start = int((self.angle + i * 120) * 16)
            painter.drawArc(int(cx-120), int(cy-120), 240, 240, start, 60 * 16)
            
        if self.state == "speaking":
            painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
            path = QPainterPath()
            for x in range(-50, 51):
                y = (30 + self.pulse * 20) * math.sin(x * 0.2 + time.time() * 10)
                if x == -50: path.moveTo(cx + x, cy + y)
                else: path.lineTo(cx + x, cy + y)
            painter.drawPath(path)


class FaceVerificationWidget(QWidget):
    """Face verification with Aspect Ratio Fix & SUCCESS STATE"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.scan_progress = 0
        self.scanning = False
        self.success = False 
        self.camera_frame = None 
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(24) 
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
    
    def start_scan(self):
        self.scanning = True
        self.success = False
        self.scan_progress = 0
        self.camera_frame = None
    
    def stop_scan(self):
        self.scanning = False
        self.camera_frame = None
        self.update()
    
    def set_success(self):
        self.success = True
        self.scanning = False
        self.update()

    def update_image(self, image):
        self.camera_frame = image
        self.update()
    
    def animate(self):
        self.angle = (self.angle + 2) % 360
        if self.scanning:
            self.scan_progress = min(self.scan_progress + 1, 100)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 200, 200
        
        if self.success:
            main_color = QColor(0, 255, 0)
            glow_color = QColor(0, 255, 0, 100)
        else:
            main_color = QColor(0, 180, 255)
            glow_color = QColor(0, 180, 255, 100)

        if self.camera_frame and self.scanning and not self.success:
            path = QPainterPath()
            path.addEllipse(QPointF(cx, cy), 110, 110)
            painter.setClipPath(path)
            
            img_x = int(cx - self.camera_frame.width() / 2)
            img_y = int(cy - self.camera_frame.height() / 2)
            painter.drawImage(img_x, img_y, self.camera_frame)
            painter.setClipping(False)

        for i in range(3):
            radius = 120 + i * 30
            if self.success:
                color = main_color
                color.setAlpha(150)
            else:
                angle_offset = (self.angle + i * 90) % 360
                alpha = int(100 + 100 * abs(math.sin(math.radians(angle_offset))))
                color = QColor(main_color.red(), main_color.green(), main_color.blue(), alpha)
            
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        if self.scanning and not self.success:
            scan_angle = (self.angle * 3) % 360
            length = 140
            x = cx + length * math.cos(math.radians(scan_angle))
            y = cy + length * math.sin(math.radians(scan_angle))
            gradient = QLinearGradient(cx, cy, x, y)
            gradient.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), 200))
            gradient.setColorAt(1, QColor(main_color.red(), main_color.green(), main_color.blue(), 0))
            painter.setPen(QPen(QBrush(gradient), 3))
            painter.drawLine(cx, cy, int(x), int(y))
        
        if not self.camera_frame or self.success:
            gradient = QRadialGradient(cx, cy, 80)
            gradient.setColorAt(0, glow_color)
            gradient.setColorAt(1, Qt.GlobalColor.transparent)
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - 80, cy - 80, 160, 160)
            
            if self.success:
                painter.setPen(QPen(QColor(255, 255, 255), 5))
                painter.drawLine(cx - 20, cy, cx - 5, cy + 20)
                painter.drawLine(cx - 5, cy + 20, cx + 30, cy - 30)


class BlazeMainWindow(QMainWindow):
    def __init__(self):
        self._last_command = None
        super().__init__()
        self.setWindowTitle("Blaze Voice Assistant")
        self.setFixedSize(1000, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000000, stop:1 #0a0a0a);")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setup_header()
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.addWidget(self.content_widget)
        self.setup_verification_screen()
        
        self.voice_thread = None
        self.auth_thread = None
        self.auth_signals = None
        
        io.prefetch("Scanning biometric data")
        io.prefetch("Access denied")
        io.prefetch("Access granted")
        io.prefetch(f"Welcome back, {config.USER_NAME}.")
        
        QTimer.singleShot(1500, self.start_authentication)
    
    def setup_header(self):
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background: rgba(15, 15, 25, 200);")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        title = QLabel("● Blaze")
        title.setFont(QFont("Helvetica", 28, QFont.Weight.Light))
        title.setStyleSheet("color: #5AB4FF; background: transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setColor(QColor(90, 180, 255, 180))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        layout.addWidget(title)
        layout.addStretch()
        close_btn = QLabel("×")
        close_btn.setFixedSize(40, 40)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setFont(QFont("Helvetica", 32, QFont.Weight.Light))
        close_btn.setStyleSheet("color: #888;")
        close_btn.mousePressEvent = lambda e: self.close()
        layout.addWidget(close_btn)
        self.main_layout.addWidget(header)
    
    def setup_verification_screen(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)
        self.face_widget = FaceVerificationWidget()
        layout.addWidget(self.face_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("Initializing Security Protocols")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica", 20, QFont.Weight.Light))
        self.status_label.setStyleSheet("color: #5AB4FF;")
        layout.addWidget(self.status_label)
        self.progress_label = QLabel("Awaiting biometric input...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Helvetica", 14))
        self.progress_label.setStyleSheet("color: #666;")
        layout.addWidget(self.progress_label)
        self.content_layout.addWidget(container)

    def start_authentication(self):
        self.update_status("SCANNING BIOMETRICS")
        self.face_widget.start_scan()
        
        self.auth_signals = FaceAuthSignals()
        self.auth_signals.status_changed.connect(self.update_status)
        self.auth_signals.progress_changed.connect(self.update_progress)
        self.auth_signals.auth_result.connect(self.handle_auth_result)
        self.auth_signals.cam_update.connect(self.face_widget.update_image)
        
        self.auth_thread = FaceAuthThread(self.auth_signals)
        self.auth_thread.start()
        
    def handle_auth_result(self, verified):
        self.face_widget.stop_scan()
        if verified:
            self.face_widget.set_success()
            self.update_status("ACCESS GRANTED")
            self.update_progress("Identity Verified")
            QTimer.singleShot(1000, self.play_boot_sequence)
        else:
            self.update_status("ACCESS DENIED")
            self.update_progress("Intruder Detected")
            io.speak("Access denied.")

    def play_boot_sequence(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.boot_widget = BootSequenceWidget()
        self.boot_widget.finished.connect(self.on_boot_finished)
        self.content_layout.addWidget(self.boot_widget)

    def on_boot_finished(self):
        io.speak(f"Welcome back, {config.USER_NAME}.")
        self.setup_assistant_screen()
        self.start_voice_listening()

    def setup_assistant_screen(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        # --- HUD LAYOUT ---
        main_hud = QVBoxLayout()
        
        # Top Bar: Clock & Stats
        top_bar = QHBoxLayout()
        self.clock = HUDClock()
        self.sys_monitor = SystemMonitor()
        top_bar.addWidget(self.clock)
        top_bar.addStretch()
        top_bar.addWidget(self.sys_monitor)
        main_hud.addLayout(top_bar)
        
        # Center: Orb
        self.orb = SiriOrb()
        main_hud.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Bottom: Command Log
        self.command_log = QLabel('Say "Blaze" to activate')
        self.command_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.command_log.setFont(QFont("Helvetica", 16, QFont.Weight.Light))
        self.command_log.setStyleSheet("color: #5AB4FF; padding: 10px;")
        self.command_log.setWordWrap(True)
        main_hud.addWidget(self.command_log)
        
        subtitle = QLabel("System Online • Listening")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Helvetica", 12))
        subtitle.setStyleSheet("color: #555;")
        main_hud.addWidget(subtitle)

        container = QWidget()
        container.setLayout(main_hud)
        self.content_layout.addWidget(container)
    
    def update_status(self, text):
        if hasattr(self, 'status_label'): self.status_label.setText(text)
    def update_progress(self, text):
        if hasattr(self, 'progress_label'): self.progress_label.setText(text)
    
    def add_log(self, text):
        text = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}"
        """Adds text to the command log with fading history effect"""
        current_text = self.command_log.text()
        # Keep last 3 lines essentially
        lines = current_text.split('\n')
        if len(lines) > 2:
            lines = lines[-2:]
        new_text = "\n".join(lines) + "\n> " + text
        self.command_log.setText(new_text.strip())

    def start_voice_listening(self):
        self.orb.set_state("listening")
        self.voice_thread = VoiceThread()
        self.voice_thread.command_received.connect(self.process_command)
        self.voice_thread.start()
    
    def process_command(self, command):
        command = command.lower().strip()
        if not command or command == 'none':
            return
        self.add_log(f"Processing: {command}")
        
        if "blaze" in command:
            self.orb.set_state("speaking")
            
            # --- SYSTEM COMMANDS ---
            if "shutdown" in command:
                io.speak("Are you sure you want to shut down?")
                self.add_log("Shutting down...")
                io.speak("Shutting down. Goodbye.")
                QTimer.singleShot(2000, lambda: automation.shutdown_system())
                QTimer.singleShot(2500, self.close)
            
            elif "restart" in command or "reboot" in command:
                self.add_log("Restarting...")
                io.speak("Restarting system.")
                automation.restart_system()
                QTimer.singleShot(1000, self.close)
            
            elif "sleep" in command:
                io.speak("Going to sleep.")
                automation.sleep_system()
                QTimer.singleShot(1000, self.close)
            
            elif "stop" in command or "exit" in command:
                io.speak("Goodbye.")
                self.close()

            # --- UTILITY COMMANDS ---
            elif "open" in command:
                app = command.replace("open", "").replace("blaze", "").strip()
                self.add_log(f"Opening {app}")
                automation.open_app(app)
            
            elif "search" in command:
                query = command.replace("search", "").replace("blaze", "").strip()
                self.add_log(f"Searching: {query}")
                automation.search_google(query)
            
            elif "screenshot" in command:
                self.add_log("Taking screenshot")
                automation.take_screenshot()

            # --- NEW FEATURES ---
            elif "time" in command:
                now = datetime.datetime.now().strftime("%I:%M %p")
                self.add_log(f"Time: {now}")
                io.speak(f"The time is {now}")

            elif "date" in command:
                today = datetime.datetime.now().strftime("%A, %B %d")
                self.add_log(f"Date: {today}")
                io.speak(f"Today is {today}")

            elif "volume" in command:
                # Basic Volume Control (Mac)
                try:
                    words = command.split()
                    for word in words:
                        if word.isdigit():
                            vol = max(0, min(100, int(word)))
                            vol = int(word)
                            os.system(f"osascript -e 'set volume output volume {vol}'")
                            self.add_log(f"Volume set to {vol}%")
                            io.speak(f"Volume set to {vol} percent.")
                            break
                except:
                    pass
            
            elif "mute" in command:
                os.system("osascript -e 'set volume output muted true'")
                self.add_log("System Muted")
            
            elif "unmute" in command:
                os.system("osascript -e 'set volume output muted false'")
                self.add_log("System Unmuted")

            elif "note" in command or "write" in command:
                io.speak("What should I write?")
                # Quick listen for the note content
                # Note: blocking call here is okay for short interactions
                note_content = io.listen() 
                if note_content != "none":
                    with open("notes.txt", "a") as f:
                        f.write(f"{datetime.datetime.now()}: {note_content}\n")
                    self.add_log("Note saved.")
                    io.speak("I've saved that note for you.")
                else:
                    io.speak("I didn't catch that.")

            QTimer.singleShot(2000, lambda: self.orb.set_state("listening"))
            
    def closeEvent(self, event):
        if hasattr(self, 'orb') and self.orb: self.orb.timer.stop()
        if hasattr(self, 'face_widget') and self.face_widget: self.face_widget.timer.stop()
        if hasattr(self, 'boot_widget') and self.boot_widget: self.boot_widget.timer.stop()
        if hasattr(self, 'sys_monitor') and self.sys_monitor: self.sys_monitor.timer.stop()
        if hasattr(self, 'clock') and self.clock: self.clock.timer.stop()
        
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
            self.voice_thread.wait(500)
        if self.auth_thread and self.auth_thread.isRunning():
            self.auth_thread.wait(500)
        event.accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = BlazeMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()