from machine import UART, Pin
import time


RX_PIN = 21
TX_PIN = 22
BAUD = 115200

print("Starting raw K210 face UART debug...")
print("ESP32 RX=GPIO21/SDA, TX=GPIO22/SCL")

uart = UART(
    1,
    baudrate=BAUD,
    bits=8,
    parity=None,
    stop=1,
    rx=Pin(RX_PIN),
    tx=Pin(TX_PIN),
    timeout=50,
)

time.sleep_ms(200)

while uart.any():
    uart.read()

# Mode 4 is face recognition in ACB_Canmv.face_recognize().
print("Sending face recognition mode command: [4, 13, 10]")
uart.write(bytes([4, 13, 10]))

last_command_ms = time.ticks_ms()
last_rx_ms = time.ticks_ms()

while True:
    if uart.any():
        data = uart.read()
        last_rx_ms = time.ticks_ms()
        print("RX bytes:", list(data))

        if len(data) > 1:
            data_len = data[0]
            payload = data[1:]
            print("len byte:", data_len, "payload len:", len(payload), "payload:", list(payload))

    if time.ticks_diff(time.ticks_ms(), last_command_ms) > 2000:
        print("Resending face recognition mode command...")
        uart.write(bytes([4, 13, 10]))
        last_command_ms = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), last_rx_ms) > 3000:
        print("No UART bytes received in the last 3 seconds.")
        last_rx_ms = time.ticks_ms()

    time.sleep_ms(50)
