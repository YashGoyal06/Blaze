import cv2
import os
import numpy as np
import time

# File paths
trainer_file = "user_data/trainer.yml"
dataset_path = "user_data"

# Initialize Face Detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def is_user_registered():
    return os.path.exists(trainer_file)

def capture_and_train_qt(signals):
    """
    Captures user face using OpenCV and trains the LBPH model.
    """
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    faces_data = []
    ids = []
    count = 0
    required_samples = 50 

    signals.update_status("REGISTRATION MODE")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        signals.update_camera_frame(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            faces_data.append(gray[y:y+h, x:x+w])
            ids.append(1) 
            count += 1
            signals.update_progress(f"Capturing biometric data: {int((count/required_samples)*100)}%")

        if count >= required_samples:
            break
        
        # Timeout/Safety break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    
    if len(faces_data) > 0:
        signals.update_status("COMPUTING NEURAL MAP...")
        recognizer.train(faces_data, np.array(ids))
        recognizer.save(trainer_file)
        return True
        
    return False

def verify_user_qt(signals):
    """
    Verification with Timeout to prevent 'Stuck' state.
    """
    if not os.path.exists(trainer_file):
        return False

    signals.update_status("LOADING BIOMETRICS...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(trainer_file)
    except:
        return False

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    verified = False
    start_time = time.time() # Start timer
    timeout_seconds = 8      # Stop scanning after 8 seconds

    signals.update_status("SCANNING...")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        signals.update_camera_frame(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            id_num, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            
            # LBPH Confidence: < 85 is a match (Lower is better)
            if confidence < 85: 
                verified = True
                break 
        
        if verified:
            break

        # TIMEOUT CHECK: If 8 seconds pass, give up.
        if time.time() - start_time > timeout_seconds:
            break

    cap.release()
    return verified