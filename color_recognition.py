from libs import ACB_Canmv
import time

print("Starting K210 color recognition test...")

cam = ACB_Canmv.ACB_Canmv()

COLOR_INDEX = 0
PIXELS_TH = 200
AREA_TH = 200

cam.init(cam.SDA, cam.SCL)
print("K210 UART initialized. Waiting for color recognition...")

misses = 0

while True:
    if cam.color_recognize(COLOR_INDEX, PIXELS_TH, AREA_TH):
        print("Tag:", cam.getTag)
        print("X,Y,W,H:", cam.getX, cam.getY, cam.getW, cam.getH)
        misses = 0
    else:
        misses += 1
        if misses % 20 == 0:
            print("No color detected yet...")

    time.sleep_ms(50)
