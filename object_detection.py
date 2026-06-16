import cv2
import numpy as np
import time

net = cv2.dnn.readNet(
    "object_detection_model/weights/yolov3-tiny.weights",
    "object_detection_model/config/yolov3-tiny.cfg"
)

label_classes = []
with open("object_detection_model/objectLabels/coco.names", "r") as f:
    label_classes = [name.strip() for name in f.readlines()]

layer_names   = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
colors        = np.random.uniform(0, 255, size=(len(label_classes), 3))
font          = cv2.FONT_HERSHEY_PLAIN

FORBIDDEN_OBJECTS = ["cell phone", "book", "laptop", "remote"]
CONFIDENCE_THRESH = 0.25   # أقل شوي من 0.3 للقبض بشكل أفضل
NMS_THRESH        = 0.4


def detectObject(frame):
    """
    يكشف الأجسام ويرسم عليها.
    يرجع:
        labels_this_frame : list[(label, confidence)]
        forbidden_boxes   : list[(label, x, y, w, h)]  ← للـ overlay في الستريم
    """
    labels_this_frame = []
    forbidden_boxes   = []

    height, width, _ = frame.shape

    blob = cv2.dnn.blobFromImage(
        frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False
    )
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids, confidences, boxes = [], [], []

    for out in outs:
        for detection in out:
            scores     = detection[5:]
            class_id   = int(np.argmax(scores))
            confidence = float(scores[class_id])

            if confidence > CONFIDENCE_THRESH:
                cx = int(detection[0] * width)
                cy = int(detection[1] * height)
                w  = int(detection[2] * width)
                h  = int(detection[3] * height)
                x  = cx - w // 2
                y  = cy - h // 2
                boxes.append([x, y, w, h])
                confidences.append(confidence)
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESH, NMS_THRESH)

    for i in range(len(boxes)):
        if i in indexes:
            label = label_classes[class_ids[i]]
            conf  = confidences[i]
            labels_this_frame.append((label, conf))

            if label in FORBIDDEN_OBJECTS:
                x, y, w, h = boxes[i]
                forbidden_boxes.append((label, conf, x, y, w, h))

                # رسم على الفريم (يظهر في app.py وفي الستريم عبر cached overlay)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    f"DETECTED: {label.upper()} ({conf:.0%})",
                    (x, max(y - 8, 15)),
                    font, 1.2, (0, 0, 255), 2
                )

    # شريط حالة في أعلى الفريم
    status_color = (0, 0, 255) if forbidden_boxes else (0, 200, 0)
    status_text  = (
        "PHONE / OBJECT DETECTED!" if forbidden_boxes
        else f"Clear  ({len(labels_this_frame)} obj)"
    )
    cv2.rectangle(frame, (0, 0), (width, 28), (0, 0, 0), -1)
    cv2.putText(frame, status_text, (8, 20), font, 1.3, status_color, 2)

    return labels_this_frame, forbidden_boxes
