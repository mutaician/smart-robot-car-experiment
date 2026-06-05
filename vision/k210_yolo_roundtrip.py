import argparse
import base64
import time

import cv2
import numpy as np
import serial
from ultralytics import YOLO


def decode_frame(line):
    parts = line.split(" ", 4)
    if len(parts) == 4:
        _, width, height, encoded_payload = parts
        mode = "GRAY"
    else:
        _, mode, width, height, encoded_payload = parts

    width = int(width)
    height = int(height)
    payload = base64.b64decode(encoded_payload)

    if mode == "RGB565":
        raw = np.frombuffer(payload, dtype=np.uint16).reshape((height, width))
        raw = raw.byteswap()
        r = ((raw >> 11) & 0x1F) << 3
        g = ((raw >> 5) & 0x3F) << 2
        b = (raw & 0x1F) << 3
        frame = np.dstack((b, g, r)).astype(np.uint8)
    else:
        frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width))
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    return frame


def main():
    parser = argparse.ArgumentParser(description="K210 frame -> laptop YOLO visualization.")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--rotate", choices=["none", "180"], default="180")
    args = parser.parse_args()

    model = YOLO(args.model)
    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        print("Waiting for K210 RGB frames...")

        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line.startswith("FRAME "):
                if line:
                    print("K210:", line[:200])
                continue

            frame = decode_frame(line)
            if args.rotate == "180":
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            results = model.predict(frame, imgsz=320, conf=args.conf, verbose=False)
            boxes = results[0].boxes
            names = results[0].names

            annotated = frame.copy()
            if boxes is not None:
                for box in boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    label = names.get(cls, str(cls))

                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 1)
                    cv2.putText(
                        annotated,
                        f"{label} {conf:.2f}",
                        (x1, max(10, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.35,
                        (0, 255, 0),
                        1,
                    )

            preview = cv2.resize(annotated, (640, 480), interpolation=cv2.INTER_LINEAR)
            cv2.imshow("K210 YOLO laptop detection", preview)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
