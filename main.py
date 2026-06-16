import cv2
import time
import threading
from facial_detections import detectFace
from blink_detection import isBlinking
from mouth_tracking import mouthTrack
from object_detection import detectObject
from eye_tracker import gazeDetection
from head_pose_estimation import head_pose_detection
from datetime import datetime

font = cv2.FONT_HERSHEY_PLAIN

# ── سجل النشاط ──────────────────────────────────────────────
data_record = []
running     = True

# ── قائمة أحداث الغش ─────────────────────────────────────────
cheat_events_queue = []
cheat_events_lock  = threading.Lock()

def push_cheat_event(event_type, reason_ar, reason_en):
    with cheat_events_lock:
        cheat_events_queue.append({
            "type":   event_type,
            "reason": {"ar": reason_ar, "en": reason_en}
        })

# ── إعداد الكاميرا ───────────────────────────────────────────
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cam.set(cv2.CAP_PROP_FPS, 30)
if not cam.isOpened():
    cam.open()

# ── حالة مشتركة بين threads ──────────────────────────────────
latest_frame       = None
frame_lock         = threading.Lock()

# الـ overlay: صناديق آخر كشف تُطبَّق على كل فريم في الستريم
cached_boxes       = []
cached_boxes_lock  = threading.Lock()

# حالة الكشف الحالية (للشريط العلوي في الستريم)
detection_status   = "Initializing..."
status_lock        = threading.Lock()

# حالة الكشف المفصّلة (تُرسَل للواجهة)
detection_state = {
    "face":  "searching",   # searching / ok / multiple / none
    "gaze":  "center",      # center / left / right
    "head":  "center",      # center / left / right / up / down
    "phone": False,
    "audio": "quiet"        # quiet / loud
}
detection_state_lock = threading.Lock()

blinkCount         = 0
_detection_started = False
_audio_started     = False

# ── Cooldowns ────────────────────────────────────────────────
_cd_multiple_faces = 0
_cd_gaze_away      = 0
_cd_phone          = 0
_cd_audio          = 0
_gaze_away_since   = None
GAZE_AWAY_LIMIT    = 7.0

# ── Audio Detection Thread ────────────────────────────────────
def _audio_worker():
    global _cd_audio
    try:
        import pyaudio
        import numpy as np

        CHUNK     = 1024
        RATE      = 44100
        THRESHOLD = 2000
        COOLDOWN  = 10.0   # ثوانٍ بين كل تنبيه صوتي

        p      = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

        while running:
            try:
                data       = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude  = int(np.max(np.abs(audio_data)))
                loud       = amplitude > THRESHOLD
                now        = time.time()

                with detection_state_lock:
                    detection_state["audio"] = "loud" if loud else "quiet"

                if loud and now > _cd_audio:
                    push_cheat_event(
                        "suspicious_audio",
                        "تم اكتشاف صوت مرتفع أو كلام أثناء الامتحان!",
                        "Suspicious audio or speech detected during exam!"
                    )
                    _cd_audio = now + COOLDOWN

            except Exception:
                pass

        stream.stop_stream()
        stream.close()
        p.terminate()

    except ImportError:
        pass  # pyaudio غير مثبّت — تجاهل بصمت


def faceCount_detection(faceCount):
    if faceCount > 1:
        return "Multiple faces detected."
    elif faceCount == 0:
        return "No face detected."
    return "Face OK."


def _draw_overlay(frame):
    """يطبّق آخر نتائج الكشف على الفريم الحي."""
    h, w, _ = frame.shape

    with cached_boxes_lock:
        boxes = list(cached_boxes)

    for (label, conf, x, y, bw, bh) in boxes:
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
        cv2.putText(
            frame,
            f"DETECTED: {label.upper()} ({conf:.0%})",
            (x, max(y - 8, 15)),
            font, 1.2, (0, 0, 255), 2
        )

    with status_lock:
        st = detection_status

    bar_color = (0, 0, 180) if boxes else (0, 140, 0)
    cv2.rectangle(frame, (0, 0), (w, 26), (0, 0, 0), -1)
    cv2.putText(frame, st, (6, 19), font, 1.15, bar_color, 2)


def _detection_worker():
    global blinkCount
    global _cd_multiple_faces, _cd_gaze_away, _cd_phone
    global _gaze_away_since, detection_status, detection_state

    while running:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.1)
                continue
            frame = latest_frame.copy()

        record = [datetime.now().strftime("%H:%M:%S.%f")]
        now    = time.time()

        try:
            faceCount, faces = detectFace(frame)
            face_status = faceCount_detection(faceCount)
            record.append(face_status)

            # ── تحديث حالة الوجه ─────────────────────────────
            face_status_key = "ok" if faceCount == 1 else ("multiple" if faceCount > 1 else "none")
            with detection_state_lock:
                detection_state["face"] = face_status_key

            # ── 1. أكثر من وجه ──────────────────────────────
            if faceCount > 1 and now > _cd_multiple_faces:
                push_cheat_event(
                    "multiple_faces",
                    "تم اكتشاف أكثر من شخص في الكاميرا!",
                    "Multiple people detected in camera!"
                )
                _cd_multiple_faces = now + 15

            if faceCount == 1:

                blinkStatus = isBlinking(faces, frame)
                lbl = blinkStatus[2]
                if lbl == "Blink":
                    blinkCount += 1
                record.append(f"Blink #{blinkCount}" if lbl == "Blink" else lbl)

                eye_dir  = gazeDetection(faces, frame)
                head_dir = head_pose_detection(faces, frame)
                record.append(eye_dir)
                record.append(str(head_dir))

                # ── تحديث اتجاه النظر ────────────────────────
                gaze_key = "center"
                if head_dir in ("Head Left",)  or eye_dir == "left":  gaze_key = "left"
                if head_dir in ("Head Right",) or eye_dir == "right": gaze_key = "right"
                head_key = "center"
                if head_dir == "Head Left":  head_key = "left"
                if head_dir == "Head Right": head_key = "right"
                if head_dir == "Head Up":    head_key = "up"
                if head_dir == "Head Down":  head_key = "down"
                with detection_state_lock:
                    detection_state["gaze"] = gaze_key
                    detection_state["head"] = head_key

                # ── 2. نظر جانبي > 7 ثوانٍ ─────────────────
                looking_away = (
                    head_dir in ("Head Left", "Head Right") or
                    eye_dir  in ("left", "right")
                )
                if looking_away:
                    if _gaze_away_since is None:
                        _gaze_away_since = now
                    elif now - _gaze_away_since >= GAZE_AWAY_LIMIT and now > _cd_gaze_away:
                        push_cheat_event(
                            "gaze_away",
                            "نظرت بعيداً لأكثر من 7 ثوانٍ!",
                            "Looking away for more than 7 seconds!"
                        )
                        _cd_gaze_away    = now + 15
                        _gaze_away_since = None
                else:
                    _gaze_away_since = None

                record.append(mouthTrack(faces, frame))

                # ── 3. كشف التلفون / الأجسام (YOLO) ─────────
                labels, forbidden = detectObject(frame)
                record.append(str(labels))

                # حفظ الـ boxes للـ overlay
                with cached_boxes_lock:
                    cached_boxes.clear()
                    cached_boxes.extend(forbidden)

                # تحديث شريط الحالة
                if forbidden:
                    status_txt = f"PHONE/OBJECT: {', '.join(l for l,*_ in forbidden)}"
                else:
                    status_txt = f"OK | face:{faceCount} | eye:{eye_dir} | head:{head_dir}"

                with status_lock:
                    detection_status = status_txt

                detected_labels = [l for l, _ in labels]
                phone_now = "cell phone" in detected_labels
                with detection_state_lock:
                    detection_state["phone"] = phone_now

                if phone_now and now > _cd_phone:
                    push_cheat_event(
                        "phone",
                        "تم اكتشاف هاتف محمول أثناء الامتحان!",
                        "Mobile phone detected during exam!"
                    )
                    _cd_phone = now + 10

            else:
                with cached_boxes_lock:
                    cached_boxes.clear()
                with status_lock:
                    detection_status = face_status
                with detection_state_lock:
                    detection_state["gaze"]  = "center"
                    detection_state["head"]  = "center"
                    detection_state["phone"] = False

        except Exception as e:
            with status_lock:
                detection_status = f"Error: {e}"
            record.append(f"Detection error: {e}")

        data_record.append(record)
        time.sleep(0.5)


def proctoringAlgo():
    global latest_frame, _detection_started, _audio_started

    if not _detection_started:
        _detection_started = True
        threading.Thread(target=_detection_worker, daemon=True).start()

    if not _audio_started:
        _audio_started = True
        threading.Thread(target=_audio_worker, daemon=True).start()

    while running:
        ret, frame = cam.read()
        if not ret:
            time.sleep(0.03)
            continue

        with frame_lock:
            latest_frame = frame.copy()

        # طبّق الـ overlay (بنفس الفريم الحي → ستريم سلس + تعليقات محدّثة)
        _draw_overlay(frame)

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes()
            + b'\r\n'
        )
        time.sleep(0.033)  # ~30 FPS cap

    cam.release()


def main_app():
    activityVal = "\n".join(map(str, data_record))
    with open('activity.txt', 'w') as f:
        f.write(activityVal)
