import cv2
import time
import threading
from facial_detections import detectFace
from object_detection import detectObject
from eye_tracker import gazeDetection
from head_pose_estimation import head_pose_detection
from blink_detection import isBlinking
from mouth_tracking import mouthTrack
from datetime import datetime

font = cv2.FONT_HERSHEY_PLAIN

data_record  = []
blinkCount   = 0
running      = True

# ── Audio state ───────────────────────────────────────────────
audio_status  = "Quiet"   # "Quiet" or "LOUD"
audio_lock    = threading.Lock()
_audio_cd     = 0         # cooldown timestamp

def _audio_worker():
    global audio_status, _audio_cd
    try:
        import pyaudio, numpy as np
        CHUNK = 1024; RATE = 44100; THRESHOLD = 2000; COOLDOWN = 10.0
        p      = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)
        while running:
            try:
                data      = stream.read(CHUNK, exception_on_overflow=False)
                arr       = np.frombuffer(data, dtype=np.int16)
                amplitude = int(np.max(np.abs(arr)))
                loud = amplitude > THRESHOLD
                now  = time.time()
                with audio_lock:
                    audio_status = "LOUD" if loud else "Quiet"
                if loud and now > _audio_cd:
                    print(f"  ⚠ AUDIO: suspicious sound detected (amplitude={amplitude})")
                    _audio_cd = now + COOLDOWN
            except Exception:
                pass
        stream.stop_stream(); stream.close(); p.terminate()
    except ImportError:
        print("  [audio] pyaudio not installed — skipping audio detection")

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
if not cam.isOpened():
    cam.open()


def proctoringAlgo():
    global blinkCount, running

    threading.Thread(target=_audio_worker, daemon=True).start()
    print("=== Proctoring started — press Q to quit ===")

    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        record = [datetime.now().strftime("%H:%M:%S.%f")]
        h, w, _ = frame.shape

        # ── كشف الوجه ────────────────────────────────────────
        faceCount, faces = detectFace(frame)
        print(f"Faces: {faceCount}")
        record.append(faceCount)

        if faceCount > 1:
            cv2.putText(frame, "WARNING: Multiple faces!", (10, h - 40),
                        font, 1.5, (0, 0, 255), 2)

        if faceCount == 1:
            blinkStatus = isBlinking(faces, frame)
            if blinkStatus[2] == "Blink":
                blinkCount += 1
            record.append(blinkStatus[2])

            eye_dir  = gazeDetection(faces, frame)
            head_dir = head_pose_detection(faces, frame)
            record.append(eye_dir)
            record.append(str(head_dir))

            mouth = mouthTrack(faces, frame)
            record.append(mouth)

        # ── كشف التلفون / الأجسام ─────────────────────────────
        labels, forbidden = detectObject(frame)
        record.append(str(labels))

        if forbidden:
            print(f"  ⚠ FORBIDDEN OBJECTS: {[l for l,*_ in forbidden]}")
        else:
            print(f"  Objects: {[l for l,_ in labels] or 'none'}")

        # ── حالة الصوت ───────────────────────────────────────
        with audio_lock:
            a_status = audio_status
        record.append(f"Audio:{a_status}")

        color = (0, 0, 255) if a_status == "LOUD" else (0, 200, 0)
        cv2.putText(frame, f"Audio: {a_status}", (10, 55), font, 1.4, color, 2)

        data_record.append(record)

        # ── عرض الفريم ───────────────────────────────────────
        cv2.imshow("Proctoring Test", frame)
        if cv2.waitKey(150) & 0xFF == ord('q'):  # ~6-7 FPS
            break

    running = False
    cam.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    proctoringAlgo()

    activityVal = "\n".join(map(str, data_record))
    with open('activity.txt', 'w') as f:
        f.write(activityVal)
    print("Activity saved to activity.txt")
