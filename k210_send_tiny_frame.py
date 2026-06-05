import lcd
import sensor
import sys
import time
import ubinascii

STREAM_W = 80
STREAM_H = 60

lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(1)
sensor.set_hmirror(1)
sensor.skip_frames(time=1000)

print("K210 tiny frame sender started.")
print("Sending", STREAM_W, "x", STREAM_H, "RGB565 color frames over USB serial as base64 lines.")

while True:
    img = sensor.snapshot()
    lcd.display(img)

    small = img.resize(STREAM_W, STREAM_H)
    data = small.to_bytes()
    encoded = ubinascii.b2a_base64(data).strip()

    sys.stdout.write("FRAME RGB565 %d %d " % (STREAM_W, STREAM_H))
    sys.stdout.write(encoded.decode())
    sys.stdout.write("\n")

    time.sleep_ms(300)
