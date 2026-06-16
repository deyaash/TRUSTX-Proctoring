import cv2
import dlib
from facial_detections import detectFace


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    ret, frame = cap.read()
    frame = cv2.resize(frame, (640, 480)) 
    if not ret:
        print("Can't receive frame. Exiting ...")
        break

    try:
        faceCount, faces = detectFace(frame)
        
        
        cv2.imshow('AI Proctoring Test', frame)
    except Exception as e:
        print(f"Error during detection: {e}")
        break

    
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()