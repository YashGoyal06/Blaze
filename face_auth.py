import cv2
import os
import numpy as np
import time

# Create storage directory if not exists
if not os.path.exists('user_data'):
    os.makedirs('user_data')

FACE_FILE = "user_data/trainer.yml"

def get_face_detector():
    return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def is_user_registered():
    return os.path.exists(FACE_FILE)

def capture_and_train_qt(window):
    """
    Captures user faces and trains the LBPH Recognizer for PyQt6.
    """
    detector = get_face_detector()
    video = cv2.VideoCapture(0)
    
    count = 0
    samples = []
    ids = []
    
    time.sleep(1)

    while True:
        ret, frame = video.read()
        if not ret:
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        # Draw face rectangles
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 3)
            cv2.putText(frame, f"Capturing: {count}/50", (x+5, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            
            count += 1
            samples.append(gray[y:y+h, x:x+w])
            ids.append(1)  # ID 1 is the user
        
        # Update UI
        window.update_camera_frame(frame)
        window.update_status(f"CAPTURING BIOMETRIC DATA: {count}/50")

        if count >= 50:
            break
            
    video.release()
    
    window.update_status("PROCESSING NEURAL PATTERNS...")
    time.sleep(1)

    # Train the recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(samples, np.array(ids))
    recognizer.write(FACE_FILE)
    
    window.update_status("BIOMETRIC REGISTRATION COMPLETE")
    time.sleep(1)
    return True

def verify_user_qt(window):
    """
    Verifies the user against the trained model for PyQt6.
    """
    if not is_user_registered():
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(FACE_FILE)
    
    detector = get_face_detector()
    video = cv2.VideoCapture(0)
    
    verified_frames = 0
    total_frames = 0

    start_time = time.time()
    
    # Try for 10 seconds max
    while (time.time() - start_time) < 10:
        ret, frame = video.read()
        if not ret:
            continue
        
        total_frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            id_num, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            # Confidence: Lower is better (0 = perfect match). < 55 is usually good.
            if confidence < 55:
                detected_name = "✓ AUTHORIZED"
                color = (0, 255, 0)  # Green
                verified_frames += 1
            else:
                detected_name = "✗ UNKNOWN"
                color = (0, 0, 255)  # Red

            # Draw rectangle and text
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
            cv2.putText(frame, detected_name, (x+5, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            confidence_percent = max(0, 100 - confidence)
            cv2.putText(frame, f"Match: {round(confidence_percent)}%", 
                       (x+5, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        # Update UI
        window.update_camera_frame(frame)
        window.update_status(f"SCANNING... MATCH CONFIDENCE: {verified_frames}/15")
        
        if verified_frames > 15:  # Need 15 good frames to pass
            video.release()
            return True

    video.release()
    return False