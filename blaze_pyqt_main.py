import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                          QPoint, QPointF, QRect, pyqtSignal, QThread, QParallelAnimationGroup, QSequentialAnimationGroup)
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QLinearGradient, 
                        QRadialGradient, QPainterPath, QFont, QPixmap, QImage, QPolygonF)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
import cv2
import threading
import time
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


class OpenGLOrb(QOpenGLWidget):
    """3D OpenGL Orb Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.rotation_x = 0
        self.rotation_y = 0
        self.pulse = 0
        self.pulse_direction = 1
        self.state = "idle"
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_rotation)
        self.timer.start(16)
        
        self.setMinimumSize(400, 400)
    
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Light setup
        glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 2, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
        
        glClearColor(0.04, 0.04, 0.06, 0.0)
    
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Set color based on state
        if self.state == "listening":
            base_color = (0.0, 1.0, 1.0, 0.8)  # Cyan
        elif self.state == "speaking":
            base_color = (0.0, 1.0, 0.4, 0.8)  # Green
        elif self.state == "scanning":
            base_color = (1.0, 0.6, 0.0, 0.8)  # Orange
        else:
            base_color = (0.0, 0.6, 1.0, 0.7)  # Blue
        
        # Draw main sphere
        scale = 1.0 + 0.1 * self.pulse
        glPushMatrix()
        glScalef(scale, scale, scale)
        glColor4f(*base_color)
        
        quadric = gluNewQuadric()
        gluQuadricDrawStyle(quadric, GLU_FILL)
        gluSphere(quadric, 1.0, 32, 32)
        gluDeleteQuadric(quadric)
        glPopMatrix()
        
        # Draw outer rings
        for i in range(3):
            glPushMatrix()
            ring_scale = 1.3 + i * 0.3 + 0.05 * self.pulse
            glScalef(ring_scale, ring_scale, ring_scale)
            glRotatef(self.angle + i * 120, 0, 1, 0)
            
            alpha = 0.3 - i * 0.08
            glColor4f(base_color[0], base_color[1], base_color[2], alpha)
            
            # Draw torus
            self.draw_torus(0.05, 1.0, 20, 30)
            glPopMatrix()
        
        # Draw particles for listening state
        if self.state == "listening":
            self.draw_particles()
    
    def draw_torus(self, inner_radius, outer_radius, sides, rings):
        for i in range(rings):
            glBegin(GL_QUAD_STRIP)
            for j in range(sides + 1):
                for k in range(2):
                    s = (i + k) % rings + 0.5
                    t = j % sides
                    
                    x = math.cos(t * 2 * math.pi / sides) * math.cos(s * 2 * math.pi / rings)
                    y = math.sin(t * 2 * math.pi / sides) * math.cos(s * 2 * math.pi / rings)
                    z = math.sin(s * 2 * math.pi / rings)
                    
                    glVertex3f(
                        x * (outer_radius + inner_radius * math.cos(s * 2 * math.pi / rings)),
                        y * (outer_radius + inner_radius * math.cos(s * 2 * math.pi / rings)),
                        inner_radius * z
                    )
            glEnd()
    
    def draw_particles(self):
        glDisable(GL_LIGHTING)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        
        for i in range(50):
            angle1 = (self.angle + i * 7.2) * math.pi / 180
            angle2 = (i * 3.6) * math.pi / 180
            distance = 2.0 + 0.5 * math.sin(self.angle * math.pi / 180 + i)
            
            x = distance * math.cos(angle1) * math.sin(angle2)
            y = distance * math.sin(angle1) * math.sin(angle2)
            z = distance * math.cos(angle2)
            
            alpha = 0.5 + 0.5 * math.sin(self.angle * math.pi / 180 + i)
            glColor4f(0.0, 1.0, 1.0, alpha)
            glVertex3f(x, y, z)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    def update_rotation(self):
        self.angle = (self.angle + 1) % 360
        self.rotation_y = (self.rotation_y + 0.5) % 360
        
        self.pulse += self.pulse_direction * 0.02
        if self.pulse >= 1.0 or self.pulse <= 0.0:
            self.pulse_direction *= -1
        
        self.update()
    
    def set_state(self, state):
        self.state = state


class ScanningRing(QWidget):
    """Animated scanning ring for verification"""
    
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
        
        # Draw rotating rings
        for i in range(4):
            radius = 120 + i * 30
            angle_offset = (self.angle + i * 90) % 360
            
            # Calculate alpha based on angle
            alpha = int(100 + 100 * abs(math.sin(math.radians(angle_offset))))
            
            if self.scanning:
                color = QColor(255, 150, 0, alpha)  # Orange while scanning
            else:
                color = QColor(0, 200, 255, alpha)  # Blue when idle
            
            pen = QPen(color, 3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        # Draw scan line
        if self.scanning:
            scan_angle = (self.angle * 3) % 360
            length = 150
            x = cx + length * math.cos(math.radians(scan_angle))
            y = cy + length * math.sin(math.radians(scan_angle))
            
            pen = QPen(QColor(255, 200, 0, 200), 4)
            painter.setPen(pen)
            painter.drawLine(cx, cy, int(x), int(y))
        
        # Draw central circle
        if self.scanning:
            gradient = QRadialGradient(cx, cy, 80)
            gradient.setColorAt(0, QColor(255, 150, 0, 150))
            gradient.setColorAt(1, QColor(255, 100, 0, 0))
        else:
            gradient = QRadialGradient(cx, cy, 80)
            gradient.setColorAt(0, QColor(0, 200, 255, 150))
            gradient.setColorAt(1, QColor(0, 100, 200, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 80, cy - 80, 160, 160)
        
        # Draw face icon in center
        painter.setPen(QPen(QColor(255, 255, 255, 200), 3))
        # Head circle
        painter.drawEllipse(cx - 30, cy - 40, 60, 60)
        # Body arc
        path = QPainterPath()
        path.moveTo(cx - 40, cy + 40)
        path.quadTo(cx, cy + 60, cx + 40, cy + 40)
        painter.drawPath(path)


class HexagonPanel(QWidget):
    """Animated hexagon tech panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.hexagons = []
        
        # Generate random hexagon positions
        for i in range(12):
            x = np.random.randint(30, 170)
            y = np.random.randint(50, 350)
            size = np.random.randint(15, 40)
            speed = np.random.uniform(0.5, 2.0)
            self.hexagons.append([x, y, size, speed, 0])
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def animate(self):
        for hex_data in self.hexagons:
            hex_data[4] = (hex_data[4] + hex_data[3]) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for x, y, size, speed, angle in self.hexagons:
            path = QPainterPath()
            
            # Create hexagon using QPointF
            points = []
            for i in range(6):
                angle_rad = math.radians(60 * i + angle)
                px = x + size * math.cos(angle_rad)
                py = y + size * math.sin(angle_rad)
                points.append(QPointF(px, py))
            
            polygon = QPolygonF(points)
            path.addPolygon(polygon)
            
            # Draw with glow
            alpha = int(30 + 20 * math.sin(math.radians(angle)))
            painter.setPen(QPen(QColor(0, 255, 255, alpha), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)


class BlazeMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("BLAZE AI PROTOCOL")
        # Adjusted for MacBook Retina display
        self.setFixedSize(1344, 756)
        
        # Frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Main widget
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a14, stop:0.5 #0f0a1f, stop:1 #0a0f1f);
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(15)
        
        # Top bar
        self.setup_top_bar()
        
        # Content area (will switch between verification and assistant)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_widget)
        
        # Create both screens but show verification first
        self.setup_verification_screen()
        
        # Threads
        self.voice_thread = None
        
        # Start boot sequence
        QTimer.singleShot(2000, self.start_authentication)
    
    def setup_top_bar(self):
        """Create cyberpunk-style top bar"""
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 8, 15, 8)
        
        # Title with glow effect
        title = QLabel("⚡ B L A Z E  ◢ A I ◣  P R O T O C O L")
        title.setFont(QFont("Helvetica", 24, QFont.Weight.Bold))
        title.setStyleSheet("""
            QLabel {
                color: #00ffff;
                background: transparent;
                letter-spacing: 2px;
            }
        """)
        
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor(0, 255, 255, 200))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        
        top_bar_layout.addWidget(title)
        top_bar_layout.addStretch()
        
        # System stats
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(5)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        cpu_label = QLabel("◢ CPU: ONLINE")
        cpu_label.setFont(QFont("Monaco", 10))
        cpu_label.setStyleSheet("color: #00ff88;")
        stats_layout.addWidget(cpu_label)
        
        neural_label = QLabel("◢ NEURAL: ACTIVE")
        neural_label.setFont(QFont("Monaco", 10))
        neural_label.setStyleSheet("color: #00ff88;")
        stats_layout.addWidget(neural_label)
        
        top_bar_layout.addWidget(stats_widget)
        
        # Close button
        close_btn = QLabel("◢ TERMINATE")
        close_btn.setFixedSize(120, 40)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setFont(QFont("Helvetica", 11, QFont.Weight.Bold))
        close_btn.setStyleSheet("""
            QLabel {
                color: #ff0066;
                background: rgba(255, 0, 100, 50);
                border-radius: 10px;
                border: 2px solid #ff0066;
            }
            QLabel:hover {
                background: rgba(255, 0, 100, 100);
            }
        """)
        close_btn.mousePressEvent = lambda e: self.close()
        top_bar_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(top_bar)
    
    def setup_verification_screen(self):
        """Biometric verification screen"""
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Center container
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(30)
        
        # Scanning ring animation
        self.scan_ring = ScanningRing()
        center_layout.addWidget(self.scan_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label = QLabel("◢ INITIALIZING BIOMETRIC SCAN ◣")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 100, 150, 80), 
                    stop:0.5 rgba(0, 150, 200, 100),
                    stop:1 rgba(0, 100, 150, 80));
                border: 2px solid #00ffff;
                border-radius: 12px;
                padding: 20px;
                min-width: 600px;
            }
        """)
        center_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Progress label
        self.progress_label = QLabel("◢ STANDBY ◣")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Monaco", 14))
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                background: rgba(0, 50, 100, 100);
                border: 2px solid #00aa66;
                border-radius: 10px;
                padding: 15px;
                min-width: 400px;
            }
        """)
        center_layout.addWidget(self.progress_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.content_layout.addWidget(center_container)
        
        # Pulsing animation
        self.setup_pulse_animation()
    
    def setup_assistant_screen(self):
        """Voice assistant screen"""
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Center area with 3D orb
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left hexagon panel
        self.hex_panel = HexagonPanel()
        self.hex_panel.setFixedSize(200, 400)
        center_layout.addWidget(self.hex_panel)
        
        # Center 3D Orb
        self.orb = OpenGLOrb()
        self.orb.setFixedSize(500, 500)
        center_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Right info panel
        self.setup_info_panel(center_layout)
        
        self.content_layout.addWidget(center_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status bar
        self.assistant_status = QLabel("◢ VOICE INTERFACE ACTIVE ◣")
        self.assistant_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.assistant_status.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        self.assistant_status.setStyleSheet("""
            QLabel {
                color: #00ffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 100, 150, 80), 
                    stop:0.5 rgba(0, 150, 200, 100),
                    stop:1 rgba(0, 100, 150, 80));
                border: 2px solid #00ffff;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        self.content_layout.addWidget(self.assistant_status)
        
        # Command display
        self.command_label = QLabel("◢ SAY 'BLAZE' TO ACTIVATE ◣")
        self.command_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.command_label.setFont(QFont("Monaco", 13))
        self.command_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                background: rgba(0, 50, 100, 100);
                border: 2px solid #00aa66;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.content_layout.addWidget(self.command_label)
    
    def setup_info_panel(self, layout):
        """Right side info panel"""
        info_panel = QWidget()
        info_panel.setFixedSize(200, 400)
        info_layout = QVBoxLayout(info_panel)
        info_layout.setSpacing(15)
        
        # System info boxes
        for title, value in [
            ("◢ BIOMETRIC", "VERIFIED"),
            ("◢ VOICE SYS", "ACTIVE"),
            ("◢ NEURAL NET", "ONLINE"),
            ("◢ SECURITY", "MAX")
        ]:
            box = QLabel(f"{title}\n{value}")
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setFont(QFont("Monaco", 11))
            box.setStyleSheet("""
                QLabel {
                    color: #00aaff;
                    background: rgba(0, 50, 100, 80);
                    border: 2px solid #0088cc;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            info_layout.addWidget(box)
        
        info_layout.addStretch()
        layout.addWidget(info_panel)
    
    def setup_pulse_animation(self):
        """Create pulsing effect for status label"""
        self.pulse_timer = QTimer()
        self.pulse_value = 0
        self.pulse_direction = 1
        
        def pulse():
            self.pulse_value += self.pulse_direction * 5
            if self.pulse_value >= 100 or self.pulse_value <= 0:
                self.pulse_direction *= -1
            
            alpha = 80 + int(20 * (self.pulse_value / 100))
            
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: #00ffff;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(0, 100, 150, {alpha}), 
                            stop:0.5 rgba(0, 150, 200, {alpha + 20}),
                            stop:1 rgba(0, 100, 150, {alpha}));
                        border: 2px solid #00ffff;
                        border-radius: 12px;
                        padding: 20px;
                        min-width: 600px;
                    }}
                """)
        
        self.pulse_timer.timeout.connect(pulse)
        self.pulse_timer.start(30)
    
    def update_status(self, text):
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(f"◢ {text} ◣")
    
    def update_progress(self, text):
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.setText(f"◢ {text} ◣")
    
    def update_command(self, text):
        if hasattr(self, 'command_label') and self.command_label:
            self.command_label.setText(f"◢ {text} ◣")
    
    def start_authentication(self):
        """Start face authentication"""
        self.update_status("BIOMETRIC SCAN INITIATED")
        self.scan_ring.start_scan()
        
        # Run in thread
        threading.Thread(target=self.run_face_auth, daemon=True).start()
    
    def run_face_auth(self):
        """Face authentication logic - camera runs in background"""
        time.sleep(1)
        
        if not face_auth.is_user_registered():
            self.update_status("NO USER FOUND - REGISTRATION MODE")
            self.update_progress("CAPTURING BIOMETRIC DATA...")
            io.speak("Identity not found. Initializing registration protocol.")
            success = face_auth.capture_and_train_silent(self)
            if not success:
                self.update_status("REGISTRATION FAILED")
                self.scan_ring.stop_scan()
                return
        
        self.update_status("SCANNING BIOMETRIC SIGNATURE")
        self.update_progress("ANALYZING FACIAL FEATURES...")
        io.speak("Analyzing biometric data")
        verified = face_auth.verify_user_silent(self)
        
        self.scan_ring.stop_scan()
        
        if verified:
            self.update_status("ACCESS GRANTED")
            self.update_progress("NEURAL LINK ESTABLISHED")
            time.sleep(1)
            
            # Switch to assistant screen
            QTimer.singleShot(0, self.setup_assistant_screen)
            
            io.speak(f"Welcome back, {config.USER_NAME}. All systems operational.")
            time.sleep(2)
            self.start_voice_listening()
        else:
            self.update_status("ACCESS DENIED - INTRUDER DETECTED")
            self.update_progress("SYSTEM LOCKDOWN")
            io.speak("Unknown entity. System lockdown initiated.")
    
    def start_voice_listening(self):
        """Start voice command loop"""
        self.voice_thread = VoiceThread()
        self.voice_thread.command_received.connect(self.process_command)
        self.voice_thread.start()
    
    def process_command(self, command):
        """Process voice commands"""
        self.update_command(f"PROCESSING: {command.upper()}")
        
        if "blaze" in command:
            self.orb.set_state("speaking")
            
            if "shutdown" in command or "shut down" in command:
                self.update_command("INITIATING SYSTEM SHUTDOWN")
                io.speak("Shutting down all systems. Goodbye.")
                QTimer.singleShot(2000, lambda: automation.shutdown_system())
                QTimer.singleShot(2500, self.close)
            
            elif "restart" in command or "reboot" in command:
                self.update_command("SYSTEM RESTART INITIATED")
                io.speak("Restarting all systems.")
                automation.restart_system()
                QTimer.singleShot(1000, self.close)
            
            elif "sleep" in command:
                io.speak("Entering sleep mode.")
                automation.sleep_system()
                QTimer.singleShot(1000, self.close)
            
            elif "open" in command:
                app = command.replace("open", "").replace("blaze", "").strip()
                self.update_status(f"◢ LAUNCHING: {app.upper()} ◣")
                automation.open_app(app)
            
            elif "search" in command:
                query = command.replace("search", "").replace("blaze", "").strip()
                self.update_status(f"◢ SEARCHING: {query.upper()} ◣")
                automation.search_google(query)
            
            elif "screenshot" in command:
                self.update_status("◢ CAPTURING SCREEN ◣")
                automation.take_screenshot()
            
            elif "stop" in command or "exit" in command:
                io.speak("Terminating neural link. Goodbye.")
                self.close()
            
            QTimer.singleShot(2000, lambda: self.orb.set_state("listening"))
            QTimer.singleShot(2000, lambda: self.update_status("◢ VOICE INTERFACE ACTIVE ◣"))
    
    def closeEvent(self, event):
        """Clean up on close"""
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