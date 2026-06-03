from libs import ACB_Canmv
import time


print("Starting K210 face recognition test...")

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

print("K210 UART initialized.")
print("If the K210 screen says to press S2, center the face/card and press S2 to register it.")
print("After registration, show the same face/card again and watch for ID output.")

misses = 0

while True:
    if cam.face_recognize():
        print("Tag:", cam.getTag)
        print("CX:", cam.getCX)
        print("CY:", cam.getCY)
        print("W:", cam.getW)
        print("H:", cam.getH)
        print()
        misses = 0
    else:
        misses += 1
        if misses % 20 == 0:
            print("No registered face result yet...")

    time.sleep_ms(50)
