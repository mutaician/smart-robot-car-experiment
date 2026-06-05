from machine import UART, Pin
import time


uart = UART(
    1,
    baudrate=115200,
    bits=8,
    parity=None,
    stop=1,
    rx=Pin(21),
    tx=Pin(22),
    timeout=50,
)

print("Starting raw K210 image-recognition UART debug...")
print("Sending image-recognition mode command: [5, 13, 10]")

while uart.any():
    uart.read()

uart.write(bytes([5, 13, 10]))

last_command_ms = time.ticks_ms()
last_rx_ms = time.ticks_ms()

while True:
    if uart.any():
        data = uart.read()
        last_rx_ms = time.ticks_ms()
        print("RX len:", len(data), "bytes:", list(data[:80]))

        if len(data) > 1:
            print("length byte:", data[0], "payload preview:", list(data[1:40]))

    if time.ticks_diff(time.ticks_ms(), last_command_ms) > 2000:
        uart.write(bytes([5, 13, 10]))
        print("resent mode command")
        last_command_ms = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), last_rx_ms) > 3000:
        print("No UART bytes received in the last 3 seconds.")
        last_rx_ms = time.ticks_ms()

    time.sleep_ms(50)
