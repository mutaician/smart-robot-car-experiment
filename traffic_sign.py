from libs import ACB_Canmv
from libs import vehicle
import time

cam = ACB_Canmv.ACB_Canmv()
cam.init(cam.SDA, cam.SCL)

car = vehicle.ACB_Vehicle()
car.Move(car.Stop, 0)

tag = "None"
lastTagChangeTime = time.ticks_ms()

def Car_task():
    global tag

    if tag == "Go_Straight":
        car.Move(car.Forward, 180)
        time.sleep_ms(500)

    elif tag == "Turn_Right":
        car.Move(car.Clockwise, 180)
        time.sleep_ms(500)

    elif tag == "Turn_Left":
        car.Move(car.Contrarotate, 180)
        time.sleep_ms(500)

    elif tag == "Turn_Around":
        car.Move(car.Forward, 180)
        time.sleep_ms(500)
        car.Move(car.Clockwise, 180)
        time.sleep_ms(1500)
        car.Move(car.Forward, 180)
        time.sleep_ms(500)

    elif tag == "Throughout":
        car.Move(car.Stop, 180)
        time.sleep_ms(200)

    tag = "None"
    car.Move(car.Stop, 180)

while True:
    if cam.Traffic_recognize(1):
        tag = cam.getTag
        print(tag)
        lastTagChangeTime = time.ticks_ms()

    if tag != "None" and time.ticks_diff(time.ticks_ms(), lastTagChangeTime) > 500:
        Car_task()

    time.sleep_ms(20)