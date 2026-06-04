from libs import ACB_Canmv
import time

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

while True:
    if cam.image_recognize():
        print(cam.getTag)
    time.sleep_ms(50)