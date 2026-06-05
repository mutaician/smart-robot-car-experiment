import lcd
import sensor
import time

lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(1)
sensor.set_hmirror(1)
sensor.skip_frames(time=1000)

while True:
    img = sensor.snapshot()
    img.draw_string(10, 10, "custom K210 script", color=(255, 0, 0), scale=2)
    lcd.display(img)
    time.sleep_ms(50)
