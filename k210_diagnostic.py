from libs import ACB_Canmv
import time


print("Starting K210 UART diagnostic...")

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

print("UART initialized on ESP32 RX=GPIO21/SDA, TX=GPIO22/SCL")
print("Testing K210 RGB light. It should change red, green, blue.")

for red, green, blue, name in (
    (255, 0, 0, "red"),
    (0, 255, 0, "green"),
    (0, 0, 255, "blue"),
    (0, 0, 0, "off"),
):
    print("RGB:", name)
    cam.RGB_set(red, green, blue)
    time.sleep_ms(700)

print("Polling color recognition with COLOR_INDEX=0 (all colors).")
print("Show a red, green, or blue object/card to the camera.")

misses = 0

while True:
    if cam.color_recognize(0, 50, 50):
        print("Detected:", cam.getTag)
        print("X,Y,W,H,CX,CY:", cam.getX, cam.getY, cam.getW, cam.getH, cam.getCX, cam.getCY)
        misses = 0
    else:
        misses += 1
        if misses % 20 == 0:
            print("No frame/detection yet...")

    time.sleep_ms(50)
