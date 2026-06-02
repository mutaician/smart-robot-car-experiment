from libs import ACB_Canmv
from libs import vehicle
import time


print("Starting K210 color tracking test...")

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)
cam.RGB_set(0, 0, 0, force=True)
print("K210 RGB LED turned off.")

car = vehicle.ACB_Vehicle()
car.Move(car.Stop, 0)

# K210 color indexes:
# 0 = all colors, 1 = red, 2 = green, 3 = blue.
# Blue was the most reliable color in local testing.
COLOR_INDEX = 3
PIXELS_TH = 50
AREA_TH = 50

X_STOP_MIN = 110
X_STOP_MAX = 210
H_STOP_MIN = 45
H_STOP_MAX = 80
SPEED = 120

FRAME_W = 320
FRAME_H = 240
MIN_BOX_W = 12
MIN_BOX_H = 12
MAX_BOX_W = 220
MAX_BOX_H = 170
MAX_BOX_AREA_RATIO = 0.45
REQUIRED_STABLE_FRAMES = 2

last_seen_ms = time.ticks_ms()
misses = 0
stable_frames = 0

print("Tracking blue objects. Move a blue card/object in front of the K210 camera.")


def valid_target():
    box_area = cam.getW * cam.getH
    frame_area = FRAME_W * FRAME_H

    if cam.getW < MIN_BOX_W or cam.getH < MIN_BOX_H:
        return False

    if cam.getW > MAX_BOX_W or cam.getH > MAX_BOX_H:
        return False

    if box_area / frame_area > MAX_BOX_AREA_RATIO:
        return False

    return True

while True:
    if cam.color_recognize(COLOR_INDEX, PIXELS_TH, AREA_TH):
        x = cam.getCX
        height = cam.getH
        misses = 0

        if not valid_target():
            stable_frames = 0
            print(
                "Rejected noisy target:",
                "tag =", cam.getTag,
                "x =", cam.getX,
                "y =", cam.getY,
                "w =", cam.getW,
                "h =", cam.getH,
                "cx =", cam.getCX,
            )
            car.Move(car.Stop, 0)
            time.sleep_ms(50)
            continue

        stable_frames += 1
        print("accepted", "tag =", cam.getTag, "cx =", x, "height =", height, "stable =", stable_frames)

        if stable_frames < REQUIRED_STABLE_FRAMES:
            car.Move(car.Stop, 0)
            time.sleep_ms(50)
            continue

        if x < X_STOP_MIN:
            print("turn left")
            car.Move(car.Contrarotate, SPEED)
        elif x > X_STOP_MAX:
            print("turn right")
            car.Move(car.Clockwise, SPEED)
        elif height > H_STOP_MAX:
            print("move backward")
            car.Move(car.Backward, SPEED)
        elif height < H_STOP_MIN:
            print("move forward")
            car.Move(car.Forward, SPEED)
        else:
            print("stop")
            car.Move(car.Stop, 0)

        last_seen_ms = time.ticks_ms()
    else:
        misses += 1
        stable_frames = 0
        if time.ticks_diff(time.ticks_ms(), last_seen_ms) > 250:
            car.Move(car.Stop, 0)

        if misses % 20 == 0:
            print("No color target detected. Stopped.")

    time.sleep_ms(50)
