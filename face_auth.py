import cv2
import os
import numpy as np
from threading import Thread
import time

# Create storage directory if not exists
if not os.path.exists('user_data'):
    os.makedirs('user_data')

FACE_FILE = "user_data/trainer.yml"

def get_face_detector():
    return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def is_user_registered():
    return os.path.exists(FACE_FILE)

def capture_and_train(app_instance):
    """
    Captures user faces and trains the LBPH Recognizer.
    Updates the GUI app_instance with messages.
    """
    detector = get_face_detector()
    video = cv2.VideoCapture(0)
    
    count = 0
    samples = []
    ids = []
    
    app_instance.log(">> INITIALIZING BIOMETRIC CAPTURE...")
    app_instance.speak("Please look at the camera. I need to learn your face.")

    while True:
        ret, frame = video.read()
        if not ret: continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        # Show live feed in GUI
        app_instance.display_frame(frame)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
            count += 1
            
            # Save the captured face
            samples.append(gray[y:y+h, x:x+w])
            ids.append(1) # ID 1 is the Admin
            
            # visual feedback
            cv2.putText(frame, f"Scanning: {count}%", (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1)
            app_instance.display_frame(frame) # Update GUI again with rectangle

        if count >= 50: # Take 50 samples
            break
            
    video.release()
    app_instance.log(">> PROCESSING BIOMETRIC DATA...")
    app_instance.speak("Analyzing facial features...")

    # Train the recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(samples, np.array(ids))
    recognizer.write(FACE_FILE)
    
    app_instance.log(">> REGISTRATION COMPLETE.")
    app_instance.speak("Registration successful. I now know who you are.")
    return True

def verify_user(app_instance):
    """
    Verifies the user against the trained model.
    """
    if not is_user_registered():
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(FACE_FILE)
    
    detector = get_face_detector()
    video = cv2.VideoCapture(0)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    verified_frames = 0
    
    app_instance.log(">> VERIFYING IDENTITY...")
    app_instance.speak("Scanning...")

    start_time = time.time()
    
    # Try for 10 seconds max
    while (time.time() - start_time) < 10:
        ret, frame = video.read()
        if not ret: continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.2, 5)

        detected_name = "UNKNOWN"
        color = (0, 0, 255) # Red

        for (x, y, w, h) in faces:
            id_num, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            # Confidence: Lower is better (0 = perfect match). < 50 is usually good.
            if confidence < 55: 
                detected_name = "OWNER"
                color = (0, 255, 0) # Green
                verified_frames += 1
            else:
                detected_name = "UNKNOWN"
                color = (0, 0, 255) # Red

            # Draw "Iron Man" style HUD
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, str(detected_name), (x+5, y-5), font, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Conf: {round(100 - confidence)}%", (x+5, y+h+25), font, 1, (255, 255, 0), 1)

        app_instance.display_frame(frame)
        
        if verified_frames > 10: # Need 10 good frames to pass
            video.release()
            app_instance.clear_camera_view()
            return True

    video.release()
    app_instance.clear_camera_view()
    return False