# 🔥 Blaze Voice Assistant

<div align="center">

**A futuristic, AI-powered voice assistant with facial recognition authentication**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

*Arc Reactor-inspired interface • Biometric Security • Voice-Controlled Automation*

</div>

---

## ✨ Features

### 🎭 Facial Recognition Authentication
- **Biometric Security**: LBPH face recognition for secure access
- **Auto-Registration**: First-time setup captures and trains your facial data
- **Real-Time Verification**: Live camera feed with animated scanning effects
- **Visual Feedback**: Arc reactor-style UI with success/failure indicators

### 🎤 Voice Command System
- **Wake Word Activation**: Say "Blaze" to activate commands
- **Natural Language Processing**: Understands conversational commands
- **Offline Speech Recognition**: Works without constant internet connection
- **Audio Caching**: Lightning-fast TTS responses using edge-tts

### 🖥️ System Control
- **Application Launcher**: Open any Mac application by voice
- **Web Search**: "Search [query]" to search Google instantly
- **Screenshot Capture**: Take screenshots with voice commands
- **Volume Control**: Adjust system volume, mute/unmute
- **Power Management**: Shutdown, restart, or sleep your system
- **Note Taking**: Dictate and save notes automatically

### 🎨 Futuristic UI
- **Arc Reactor Orb**: Animated assistant visualization with multiple states
- **HUD Clock**: Real-time date and time display
- **System Monitor**: Live CPU and RAM usage with circular progress bars
- **Boot Sequence**: Cinematic startup animation with sound effects
- **Command Log**: Real-time activity feed with timestamps
- **Glassmorphism**: Modern, translucent design elements

---

## 📋 Prerequisites

### System Requirements
- **OS**: macOS (designed for Mac-specific features)
- **Python**: 3.8 or higher
- **Webcam**: Required for facial recognition
- **Microphone**: Required for voice commands
- **Audio Output**: Required for voice feedback

### Python Dependencies
```bash
# Core UI Framework
PyQt6>=6.0.0

# Computer Vision
opencv-python>=4.5.0
opencv-contrib-python>=4.5.0

# Speech Recognition
SpeechRecognition>=3.8.0
edge-tts>=6.0.0
pyaudio>=0.2.11

# Automation
pywhatkit>=5.3
pyautogui>=0.9.53

# System Monitoring (Optional)
psutil>=5.8.0

# Utilities
numpy>=1.21.0
```

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/blaze-assistant.git
cd blaze-assistant
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Settings
Edit `config.py` to customize your assistant:
```python
ASSISTANT_NAME = "Blaze"
WAKE_WORD = "blaze"
USER_NAME = "Sir"  # Your preferred title
```

### 5. Launch Blaze
```bash
python blaze_pyqt_main.py
```

---

## 🎯 Usage Guide

### First Time Setup
1. **Launch Application**: Run `python blaze_pyqt_main.py`
2. **Face Registration**: The system will detect you're a new user and capture your face
3. **Stay Still**: Look at the camera while the system captures 50 samples
4. **Wait for Training**: Neural map computation takes a few seconds
5. **Access Granted**: You're now registered!

### Daily Usage
1. **Launch & Authenticate**: Your face is automatically recognized
2. **Wait for Boot Sequence**: Enjoy the cinematic startup animation
3. **Listen for "System Online"**: Voice feedback confirms readiness
4. **Give Commands**: Say "Blaze" followed by your command

### Voice Commands

#### Application Control
```
"Blaze, open Safari"
"Blaze, open Chrome"
"Blaze, open Spotify"
```

#### Web Search
```
"Blaze, search Python tutorials"
"Blaze, search weather today"
```

#### System Control
```
"Blaze, take screenshot"
"Blaze, set volume to 50"
"Blaze, mute"
"Blaze, unmute"
```

#### Information
```
"Blaze, what time is it?"
"Blaze, what's the date?"
```

#### Notes
```
"Blaze, write a note"
[Wait for prompt]
"Meeting at 3pm tomorrow"
```

#### Power Management
```
"Blaze, shutdown"
"Blaze, restart"
"Blaze, sleep"
"Blaze, stop"  # Exit application
```

---

## 📁 Project Structure

```
blaze-assistant/
│
├── blaze_pyqt_main.py      # Main application & UI
├── face_auth.py            # Facial recognition logic
├── speech_engine.py        # TTS & STT engine
├── automation.py           # System automation functions
├── config.py               # User configuration
│
├── user_data/              # Facial recognition data
│   └── trainer.yml         # Trained face model
│
├── voice_cache/            # TTS audio cache
│   └── *.mp3              # Cached voice responses
│
├── notes.txt              # User dictated notes
└── requirements.txt       # Python dependencies
```

---

## 🎨 UI Components

### Arc Reactor Orb
- **Idle State**: Slow rotation with cyan glow
- **Listening State**: Faster rotation, awaiting commands
- **Speaking State**: Waveform animation with pulse effect

### Face Verification Widget
- **Scanning Mode**: Animated rings with live camera feed
- **Success State**: Green glow with checkmark
- **Failure State**: Red indicators

### HUD Elements
- **Clock**: Real-time display with modern typography
- **System Monitor**: Circular CPU/RAM gauges
- **Command Log**: Scrolling activity feed

---

## 🔧 Customization

### Change Voice
Edit `speech_engine.py`:
```python
# Male voices
VOICE = "en-US-ChristopherNeural"  # Default
VOICE = "en-US-GuyNeural"
VOICE = "en-US-EricNeural"

# Female voices
VOICE = "en-US-JennyNeural"
VOICE = "en-US-AriaNeural"
```

### Adjust Recognition Sensitivity
Edit `face_auth.py`:
```python
# Lower = more strict, Higher = more lenient
if confidence < 85:  # Default threshold
```

### Modify Colors
Edit color schemes in `blaze_pyqt_main.py`:
```python
cyan = QColor(0, 255, 255)      # Primary accent
main_color = QColor(0, 180, 255) # Secondary
```

---

## ⚠️ Troubleshooting

### Microphone Not Working
```bash
# Test microphone access
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Grant microphone permissions in System Preferences
```

### Camera Not Working
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# Grant camera permissions in System Preferences
```

### Face Recognition Fails
- Ensure good lighting conditions
- Look directly at the camera
- Remove glasses/hats during registration
- Delete `user_data/trainer.yml` to re-register

### Voice Commands Not Recognized
- Speak clearly and at normal volume
- Check microphone sensitivity in System Preferences
- Reduce background noise
- Wait for "Listening..." confirmation

### Performance Issues
```bash
# Install psutil for system monitoring
pip install psutil

# Close unnecessary background applications
# Reduce energy_threshold in speech_engine.py
```

---

## 🔒 Security & Privacy

- **Local Processing**: All facial recognition runs locally on your machine
- **No Cloud Storage**: Face data never leaves your computer
- **Encrypted Storage**: Trainer file uses OpenCV's secure format
- **Offline Capable**: Core features work without internet
- **No Telemetry**: Zero data collection or tracking

---

## 🛠️ Development

### Adding New Commands
Edit `blaze_pyqt_main.py` in the `process_command` method:

```python
elif "your command" in command:
    self.add_log("Your action description")
    io.speak("Voice feedback")
    # Your automation code here
```

### Creating Custom Animations
Extend widget classes in `blaze_pyqt_main.py`:

```python
class YourCustomWidget(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        # Your drawing code
```

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **PyQt6**: Modern Python GUI framework
- **OpenCV**: Computer vision library
- **edge-tts**: Microsoft Edge TTS engine
- **SpeechRecognition**: Google Speech API wrapper
- **pywhatkit**: Web automation utilities

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

<div align="center">

**Made with 🔥 by the Blaze Team**

*"The future is voice-activated"*

</div>
