from libs import ACB_Canmv
import time


print("Starting K210 color recognition tuning...")

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

# Use the K210 RGB LED as a white fill light for dim rooms.
# If this washes out the card color, lower these values.
LIGHT_RED = 120
LIGHT_GREEN = 120
LIGHT_BLUE = 120
cam.RGB_set(LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, force=True)
print("K210 RGB LED set to white fill light.")

# Color indexes:
# 0 = all colors, 1 = red, 2 = green, 3 = blue.
COLOR_INDEX = 3

# Lower values are easier to trigger, higher values are stricter.
PIXELS_TH = 30
AREA_TH = 30

MIN_BOX_W = 12
MIN_BOX_H = 12
MAX_BOX_W = 240
MAX_BOX_H = 190
MAX_BOX_AREA_RATIO = 0.45

print("Target color index:", COLOR_INDEX)
print("Thresholds:", "pixels =", PIXELS_TH, "area =", AREA_TH)
print("Use a large, flat blue card in bright even light.")

misses = 0
accepted = 0
rejected = 0


def valid_target():
    box_area = cam.getW * cam.getH
    frame_area = 320 * 240

    if cam.getW < MIN_BOX_W or cam.getH < MIN_BOX_H:
        return False, "too_small"

    if cam.getW > MAX_BOX_W or cam.getH > MAX_BOX_H:
        return False, "too_large"

    if box_area / frame_area > MAX_BOX_AREA_RATIO:
        return False, "too_much_frame"

    return True, "ok"

while True:
    # Some firmware versions appear to change the RGB LED when modes change,
    # but repeatedly sending LED commands can also disturb testing. Set it once
    # at startup, then leave color recognition mode alone.

    if cam.color_recognize(COLOR_INDEX, PIXELS_TH, AREA_TH):
        ok, reason = valid_target()
        misses = 0

        if ok:
            accepted += 1
            status = "accepted"
            count = accepted
        else:
            rejected += 1
            status = "raw_rejected"
            count = rejected

        print(
            status,
            "reason =", reason,
            "tag =", cam.getTag,
            "x =", cam.getX,
            "y =", cam.getY,
            "w =", cam.getW,
            "h =", cam.getH,
            "cx =", cam.getCX,
            "cy =", cam.getCY,
            "count =", count,
        )
    else:
        misses += 1
        if misses % 20 == 0:
            print("No detection yet...")

    time.sleep_ms(50)
