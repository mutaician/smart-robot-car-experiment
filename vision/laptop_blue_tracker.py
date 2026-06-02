import argparse
import time

import cv2
import numpy as np


WINDOW_NAME = "blue tracker"
MASK_WINDOW_NAME = "blue mask"
TUNER_WINDOW_NAME = "HSV tuner"


def parse_args():
    parser = argparse.ArgumentParser(description="Laptop-side blue target tracker.")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index.")
    parser.add_argument("--min-area", type=int, default=800, help="Minimum contour area.")
    parser.add_argument("--show-mask", action="store_true", help="Show the threshold mask.")
    parser.add_argument("--tune", action="store_true", help="Show HSV threshold trackbars.")
    return parser.parse_args()


def nothing(_):
    pass


def create_tuner():
    cv2.namedWindow(TUNER_WINDOW_NAME)
    cv2.createTrackbar("H low", TUNER_WINDOW_NAME, 95, 179, nothing)
    cv2.createTrackbar("H high", TUNER_WINDOW_NAME, 130, 179, nothing)
    cv2.createTrackbar("S low", TUNER_WINDOW_NAME, 70, 255, nothing)
    cv2.createTrackbar("S high", TUNER_WINDOW_NAME, 255, 255, nothing)
    cv2.createTrackbar("V low", TUNER_WINDOW_NAME, 45, 255, nothing)
    cv2.createTrackbar("V high", TUNER_WINDOW_NAME, 255, 255, nothing)


def get_tuned_bounds():
    h_low = cv2.getTrackbarPos("H low", TUNER_WINDOW_NAME)
    h_high = cv2.getTrackbarPos("H high", TUNER_WINDOW_NAME)
    s_low = cv2.getTrackbarPos("S low", TUNER_WINDOW_NAME)
    s_high = cv2.getTrackbarPos("S high", TUNER_WINDOW_NAME)
    v_low = cv2.getTrackbarPos("V low", TUNER_WINDOW_NAME)
    v_high = cv2.getTrackbarPos("V high", TUNER_WINDOW_NAME)
    return np.array([h_low, s_low, v_low]), np.array([h_high, s_high, v_high])


def make_blue_mask(frame, tune=False):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if tune:
        lower_blue, upper_blue = get_tuned_bounds()
    else:
        # Narrower defaults than the first prototype to reduce room false positives.
        lower_blue = np.array([95, 70, 45])
        upper_blue = np.array([130, 255, 255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def find_best_target(mask, min_area):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area < best_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w == 0 or h == 0:
            continue

        aspect = w / h
        if aspect < 0.25 or aspect > 4.0:
            continue

        frame_area = mask.shape[0] * mask.shape[1]
        if area / frame_area > 0.35:
            continue

        best = (x, y, w, h, area)
        best_area = area

    return best


def draw_target(frame, target):
    x, y, w, h, area = target
    cx = x + w // 2
    cy = y + h // 2

    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
    cv2.putText(
        frame,
        f"blue target cx={cx} cy={cy} area={int(area)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    return cx, cy


def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        raise SystemExit(f"Could not open camera index {args.camera}")

    last_print = 0

    print("Laptop blue tracker started.")
    print("Press q to quit. Press p to print current HSV values when using --tune.")

    if args.tune:
        create_tuner()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera frame read failed.")
            break

        mask = make_blue_mask(frame, tune=args.tune)
        target = find_best_target(mask, args.min_area)

        if target:
            cx, cy = draw_target(frame, target)
            now = time.time()
            if now - last_print > 0.25:
                print(f"target cx={cx} cy={cy} box={target[:4]} area={int(target[4])}")
                last_print = now
        else:
            cv2.putText(
                frame,
                "no blue target",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        cv2.imshow(WINDOW_NAME, frame)
        if args.show_mask:
            cv2.imshow(MASK_WINDOW_NAME, mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("p") and args.tune:
            lower, upper = get_tuned_bounds()
            print(f"lower_blue = np.array({lower.tolist()})")
            print(f"upper_blue = np.array({upper.tolist()})")

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
