import argparse
import base64

import cv2
import numpy as np
import serial


def main():
    parser = argparse.ArgumentParser(description="Read tiny grayscale frames from K210 UART.")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--rotate", choices=["none", "180"], default="180")
    args = parser.parse_args()

    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        print("Waiting for K210 frames...")
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line.startswith("FRAME "):
                if line:
                    print("K210:", line[:200])
                continue

            try:
                parts = line.split(" ", 4)
                if len(parts) == 4:
                    _, width, height, encoded_payload = parts
                    mode = "GRAY"
                else:
                    _, mode, width, height, encoded_payload = parts

                width = int(width)
                height = int(height)
                payload = base64.b64decode(encoded_payload)
            except ValueError:
                continue

            if mode == "RGB565":
                raw = np.frombuffer(payload, dtype=np.uint16).reshape((height, width))
                raw = raw.byteswap()
                r = ((raw >> 11) & 0x1F) << 3
                g = ((raw >> 5) & 0x3F) << 2
                b = (raw & 0x1F) << 3
                frame = np.dstack((b, g, r)).astype(np.uint8)
            else:
                frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width))

            if args.rotate == "180":
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            scale = max(1, min(8, 640 // width))
            preview = cv2.resize(frame, (width * scale, height * scale), interpolation=cv2.INTER_LINEAR)
            cv2.imshow("K210 tiny frame", preview)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
