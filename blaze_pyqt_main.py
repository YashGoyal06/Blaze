import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                          QPoint, QPointF, pyqtSignal, QThread, QSequentialAnimationGroup)
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QRadialGradient, 
                        QPainterPath, QFont, QLinearGradient)
import math
import numpy as np
import time
import threading
import config
import speech_engine as io
import face_auth
import automation


class VoiceThread(QThread):
    """Thread for voice recognition"""
    command_received = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            command = io.listen()
            if command != "none":
                self.command_received.emit(command)
            time.sleep(0.1)
    
    def stop(self):
        self.running = False


class SiriOrb(QWidget):
    """Beautiful Siri-like animated orb - Pure Qt implementation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.particles = []
        self.state = "idle"  # idle, listening, speaking, thinking
        self.pulse = 0
        self.pulse_direction = 1
        
        # Generate particles
        for i in range(40):
            angle = np.random.uniform(0, 360)
            distance = np.random.uniform(0, 150)
            speed = np.random.uniform(0.5, 2.0)
            size = np.random.uniform(2, 6)
            self.particles.append({
                'angle': angle,
                'distance': distance,
                'speed': speed,
                'size': size,
                'base_distance': distance
            })
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)  # ~60 FPS
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 500)
    
    def set_state(self, state):
        """Change orb state: idle, listening, speaking, thinking"""
        self.state = state
    
    def animate(self):
        self.angle = (self.angle + 1) % 360
        
        # Pulse effect
        self.pulse += self.pulse_direction * 0.02
        if self.pulse >= 1.0 or self.pulse <= 0.0:
            self.pulse_direction *= -1
        
        # Animate particles
        for particle in self.particles:
            particle['angle'] = (particle['angle'] + particle['speed']) % 360
            
            if self.state == "listening":
                target_distance = particle['base_distance'] * 0.7
            elif self.state == "speaking":
                target_distance = particle['base_distance'] * 1.3
            elif self.state == "thinking":
                target_distance = particle['base_distance'] * (1.0 + 0.3 * math.sin(math.radians(self.angle * 2)))
            else:
                target_distance = particle['base_distance']
            
            particle['distance'] += (target_distance - particle['distance']) * 0.1
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = 250, 250
        
        # Choose colors based on state
        if self.state == "listening":
            primary_color = QColor(0, 180, 255)
            secondary_color = QColor(0, 120, 200)
        elif self.state == "speaking":
            primary_color = QColor(100, 200, 255)
            secondary_color = QColor(0, 150, 255)
        elif self.state == "thinking":
            primary_color = QColor(150, 180, 255)
            secondary_color = QColor(100, 140, 255)
        else:
            primary_color = QColor(80, 160, 240)
            secondary_color = QColor(40, 120, 200)
        
        # Draw outer glow rings
        for i in range(5):
            radius = 100 + i * 25 + self.pulse * 15
            alpha = int(40 - i * 7)
            
            gradient = QRadialGradient(cx, cy, radius)
            gradient.setColorAt(0, QColor(primary_color.red(), primary_color.green(), 
                                         primary_color.blue(), alpha))
            gradient.setColorAt(1, QColor(primary_color.red(), primary_color.green(), 
                                         primary_color.blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        # Draw particles
        for particle in self.particles:
            angle_rad = math.radians(particle['angle'])
            px = cx + particle['distance'] * math.cos(angle_rad)
            py = cy + particle['distance'] * math.sin(angle_rad)
            
            alpha = int(255 * (1.0 - particle['distance'] / 200))
            alpha = max(50, min(255, alpha))
            
            particle_gradient = QRadialGradient(px, py, particle['size'] * 2)
            particle_gradient.setColorAt(0, QColor(255, 255, 255, alpha))
            particle_gradient.setColorAt(0.5, QColor(primary_color.red(), primary_color.green(), 
                                                    primary_color.blue(), alpha))
            particle_gradient.setColorAt(1, QColor(primary_color.red(), primary_color.green(), 
                                                   primary_color.blue(), 0))
            
            painter.setBrush(QBrush(particle_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(px, py), particle['size'] * 2, particle['size'] * 2)
        
        # Draw central orb
        orb_size = 60 + self.pulse * 20
        
        orb_gradient = QRadialGradient(cx, cy, orb_size)
        orb_gradient.setColorAt(0, QColor(255, 255, 255, 200))
        orb_gradient.setColorAt(0.3, QColor(primary_color.red(), primary_color.green(), 
                                           primary_color.blue(), 255))
        orb_gradient.setColorAt(0.7, QColor(secondary_color.red(), secondary_color.green(), 
                                           secondary_color.blue(), 255))
        orb_gradient.setColorAt(1, QColor(secondary_color.red(), secondary_color.green(), 
                                         secondary_color.blue(), 180))
        
        painter.setBrush(QBrush(orb_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - orb_size, cy - orb_size, orb_size * 2, orb_size * 2)
        
        # Draw orb highlight
        highlight_gradient = QRadialGradient(cx - orb_size * 0.3, cy - orb_size * 0.3, orb_size * 0.8)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 150))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(cx - orb_size, cy - orb_size, orb_size * 2, orb_size * 2)
        
        # Draw waveform if speaking
        if self.state == "speaking":
            painter.setPen(QPen(QColor(100, 200, 255, 150), 3))
            
            path = QPainterPath()
            start_x = cx - 100
            path.moveTo(start_x, cy)
            
            for x in range(200):
                wave_x = start_x + x
                wave_y = cy + 30 * math.sin(math.radians(x * 5 + self.angle * 3))
                path.lineTo(wave_x, wave_y)
            
            painter.drawPath(path)


class FaceVerificationWidget(QWidget):
    """Face verification screen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.scan_progress = 0
        self.scanning = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
    
    def start_scan(self):
        self.scanning = True
        self.scan_progress = 0
    
    def stop_scan(self):
        self.scanning = False
    
    def animate(self):
        self.angle = (self.angle + 2) % 360
        if self.scanning:
            self.scan_progress = min(self.scan_progress + 1, 100)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = 200, 200
        
        # Outer scanning rings
        for i in range(3):
            radius = 120 + i * 30
            angle_offset = (self.angle + i * 90) % 360
            alpha = int(100 + 100 * abs(math.sin(math.radians(angle_offset))))
            
            color = QColor(0, 180, 255, alpha) if self.scanning else QColor(80, 160, 240, alpha)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        # Scanning line
        if self.scanning:
            scan_angle = (self.angle * 3) % 360
            length = 140
            x = cx + length * math.cos(math.radians(scan_angle))
            y = cy + length * math.sin(math.radians(scan_angle))
            
            gradient = QLinearGradient(cx, cy, x, y)
            gradient.setColorAt(0, QColor(0, 180, 255, 200))
            gradient.setColorAt(1, QColor(0, 180, 255, 0))
            
            pen = QPen(QBrush(gradient), 3)
            painter.setPen(pen)
            painter.drawLine(cx, cy, int(x), int(y))
        
        # Central glow
        gradient = QRadialGradient(cx, cy, 80)
        if self.scanning:
            gradient.setColorAt(0, QColor(0, 180, 255, 150))
            gradient.setColorAt(1, QColor(0, 180, 255, 0))
        else:
            gradient.setColorAt(0, QColor(80, 160, 240, 150))
            gradient.setColorAt(1, QColor(80, 160, 240, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 80, cy - 80, 160, 160)
        
        # Face icon
        painter.setPen(QPen(QColor(255, 255, 255, 220), 2.5))
        painter.drawEllipse(cx - 25, cy - 35, 50, 50)
        
        path = QPainterPath()
        path.moveTo(cx - 35, cy + 35)
        path.quadTo(cx, cy + 50, cx + 35, cy + 35)
        painter.drawPath(path)


class BlazeMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Blaze Voice Assistant")
        self.setFixedSize(1000, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Dark background
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #000000, stop:1 #0a0a0a);
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Setup UI
        self.setup_header()
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.addWidget(self.content_widget)
        
        # Start with verification
        self.setup_verification_screen()
        
        self.voice_thread = None
        
        # Start authentication after delay
        QTimer.singleShot(1500, self.start_authentication)
    
    def setup_header(self):
        """Modern header"""
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background: rgba(15, 15, 25, 200);")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo/Title
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
        
        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont("Helvetica", 24))
        self.status_dot.setStyleSheet("color: #4CAF50; background: transparent;")
        layout.addWidget(self.status_dot)
        
        status_text = QLabel("ONLINE")
        status_text.setFont(QFont("Monaco", 11))
        status_text.setStyleSheet("color: #888; background: transparent; margin-left: 5px;")
        layout.addWidget(status_text)
        
        # Close button
        close_btn = QLabel("×")
        close_btn.setFixedSize(40, 40)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setFont(QFont("Helvetica", 32, QFont.Weight.Light))
        close_btn.setStyleSheet("""
            QLabel {
                color: #888;
                background: transparent;
                border-radius: 20px;
            }
            QLabel:hover {
                color: #fff;
                background: rgba(255, 255, 255, 10);
            }
        """)
        close_btn.mousePressEvent = lambda e: self.close()
        layout.addWidget(close_btn)
        
        self.main_layout.addWidget(header)
    
    def setup_verification_screen(self):
        """Face verification UI"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)
        
        # Verification widget
        self.face_widget = FaceVerificationWidget()
        layout.addWidget(self.face_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label = QLabel("Initializing Face Recognition")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica", 20, QFont.Weight.Light))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #5AB4FF;
                background: transparent;
                padding: 15px;
            }
        """)
        
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(90, 180, 255, 150))
        glow.setOffset(0, 0)
        self.status_label.setGraphicsEffect(glow)
        
        layout.addWidget(self.status_label)
        
        # Progress text
        self.progress_label = QLabel("Please look at the camera")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Helvetica", 14))
        self.progress_label.setStyleSheet("color: #666; background: transparent;")
        layout.addWidget(self.progress_label)
        
        self.content_layout.addWidget(container)
    
    def setup_assistant_screen(self):
        """Voice assistant UI"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Siri orb
        self.orb = SiriOrb()
        layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Command label
        self.command_label = QLabel('Say "Blaze" to activate')
        self.command_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.command_label.setFont(QFont("Helvetica", 18, QFont.Weight.Light))
        self.command_label.setStyleSheet("color: #5AB4FF; background: transparent;")
        
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(90, 180, 255, 120))
        glow.setOffset(0, 0)
        self.command_label.setGraphicsEffect(glow)
        
        layout.addWidget(self.command_label)
        
        # Subtitle
        subtitle = QLabel("Listening for your command...")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Helvetica", 13))
        subtitle.setStyleSheet("color: #555; background: transparent;")
        layout.addWidget(subtitle)
        
        self.content_layout.addWidget(container)
    
    def update_status(self, text):
        if hasattr(self, 'status_label'):
            self.status_label.setText(text)
    
    def update_progress(self, text):
        if hasattr(self, 'progress_label'):
            self.progress_label.setText(text)
    
    def update_command(self, text):
        if hasattr(self, 'command_label'):
            self.command_label.setText(text)
    
    def update_camera_frame(self, frame):
        """Dummy method for face_auth compatibility"""
        pass
    
    def start_authentication(self):
        """Start face auth"""
        self.update_status("Scanning Face")
        self.face_widget.start_scan()
        threading.Thread(target=self.run_face_auth, daemon=True).start()
    
    def run_face_auth(self):
        """Face authentication logic"""
        time.sleep(1)
        
        try:
            if not face_auth.is_user_registered():
                self.update_status("No User Found - Registration Mode")
                self.update_progress("Capturing biometric data...")
                io.speak("Identity not found. Starting registration.")
                success = face_auth.capture_and_train_qt(self)
                if not success:
                    self.update_status("Registration Failed")
                    self.face_widget.stop_scan()
                    return
            
            self.update_status("Verifying Identity")
            self.update_progress("Analyzing facial features...")
            io.speak("Scanning biometric data")
            verified = face_auth.verify_user_qt(self)
            
            self.face_widget.stop_scan()
            
            if verified:
                self.update_status("Access Granted")
                self.update_progress("Welcome back")
                time.sleep(1)
                
                QTimer.singleShot(0, self.setup_assistant_screen)
                
                io.speak(f"Welcome back, {config.USER_NAME}.")
                time.sleep(1)
                self.start_voice_listening()
            else:
                self.update_status("Access Denied")
                self.update_progress("Unknown person detected")
                io.speak("Access denied.")
        except Exception as e:
            print(f"Error in face auth: {e}")
            self.update_status("Error in face recognition")
            self.face_widget.stop_scan()
    
    def start_voice_listening(self):
        """Start listening"""
        self.orb.set_state("listening")
        self.voice_thread = VoiceThread()
        self.voice_thread.command_received.connect(self.process_command)
        self.voice_thread.start()
    
    def process_command(self, command):
        """Process voice commands"""
        self.update_command(f"Processing: {command}")
        
        if "blaze" in command:
            self.orb.set_state("speaking")
            
            if "shutdown" in command or "shut down" in command:
                self.update_command("Shutting down system")
                io.speak("Shutting down. Goodbye.")
                QTimer.singleShot(2000, lambda: automation.shutdown_system())
                QTimer.singleShot(2500, self.close)
            
            elif "restart" in command or "reboot" in command:
                self.update_command("Restarting system")
                io.speak("Restarting system.")
                automation.restart_system()
                QTimer.singleShot(1000, self.close)
            
            elif "sleep" in command:
                io.speak("Going to sleep.")
                automation.sleep_system()
                QTimer.singleShot(1000, self.close)
            
            elif "open" in command:
                app = command.replace("open", "").replace("blaze", "").strip()
                self.update_command(f"Opening {app}")
                automation.open_app(app)
            
            elif "search" in command:
                query = command.replace("search", "").replace("blaze", "").strip()
                self.update_command(f"Searching: {query}")
                automation.search_google(query)
            
            elif "screenshot" in command:
                self.update_command("Taking screenshot")
                automation.take_screenshot()
            
            elif "stop" in command or "exit" in command:
                io.speak("Goodbye.")
                self.close()
            
            QTimer.singleShot(2000, lambda: self.orb.set_state("listening"))
            QTimer.singleShot(2000, lambda: self.update_command('Say "Blaze" to activate'))
    
    def closeEvent(self, event):
        if self.voice_thread:
            self.voice_thread.stop()
            self.voice_thread.wait()
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