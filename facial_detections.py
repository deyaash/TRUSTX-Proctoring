import dlib
import cv2
import os
from imutils import face_utils
import numpy as np
# تأكد من المسار الصحيح
shapePredictorModel = 'shape_predictor_model/shape_predictor_68_face_landmarks.dat'

# تعريف المتغيرات عالمياً لكن تحميلها داخل الدالة لتجنب الانهيار المفاجئ
predictor = None
faceDetector = dlib.get_frontal_face_detector()



def detectFace(frame):
    global predictor
    import numpy as np

    if frame is None:
        return 0, []

    # 1. تحويل الصورة وتجهيزها (resize لتسريع الكشف)
    scale = 0.5
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray)

    # 3. محاولة اكتشاف الوجوه
    small_faces = faceDetector(gray, 0)
    faceCount = len(small_faces)

    # تحويل إحداثيات الفريم الصغير إلى الفريم الأصلي
    inv = 1.0 / scale
    faces = [dlib.rectangle(
        int(f.left()   * inv), int(f.top()    * inv),
        int(f.right()  * inv), int(f.bottom() * inv)
    ) for f in small_faces]

    for face in faces:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

    return faceCount, faces