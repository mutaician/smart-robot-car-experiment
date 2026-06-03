from libs import ACB_Canmv
from libs import vehicle
import time

Yservo_PIN = 25
Camera_Angle = 90

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

car = vehicle.ACB_Vehicle()
car.Move(car.Stop, 0)

tag = "None"
lastTagChangeTime = time.ticks_ms()

def Car_task():
    global tag
    time.sleep_ms(1000)
    for _ in range(4):
        car.Move(car.Forward, 150)
        time.sleep_ms(300)
        car.Move(car.Contrarotate, 200)
        time.sleep_ms(300)
    tag = "None"
    car.Move(car.Stop, 0)

while True:
    if cam.face_recognize():
        tag = cam.getTag
        print(tag)
        lastTagChangeTime = time.ticks_ms()

    if tag == "ID1" and time.ticks_diff(time.ticks_ms(), lastTagChangeTime) > 500:
        Car_task()

    time.sleep_ms(20)