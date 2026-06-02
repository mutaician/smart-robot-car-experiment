# QD003 K210 MicroPython Setup Notes

These are practical setup notes for using the QD003 K210 AI expansion module with the QD001 smart robot car controller without Thonny. The editor can be VS Code; uploading and serial access can be done from the terminal with `mpremote`.

## What This Path Is

The QD003 Python tutorial code is MicroPython-style embedded code, not normal laptop Python.

Files like `libs/ACB_Canmv.py` use:

```python
from machine import UART, Pin, PWM
```

That means the code runs on the ESP32 controller board. The ESP32 then talks to the K210 vision module over UART. Do not install `machine` with `uv`; it is built into MicroPython firmware.

## Board Roles

- ESP32 controller: runs MicroPython code such as `color_recognition.py`.
- K210 vision module: runs its own firmware and performs camera/AI recognition.
- Laptop: edits files and uploads them to the ESP32 using `mpremote`.

Flow:

```text
Laptop -> upload MicroPython files to ESP32
ESP32 -> sends UART commands to K210
K210 -> processes camera/vision
ESP32 -> receives detection result and prints it over serial
```

## USB Cable Lesson

The K210 did not appear in `lsusb` with one cable, but worked with a phone USB-C cable.

Working `lsusb` output should show a CH340 serial converter:

```text
ID 1a86:7523 QinHeng Electronics CH340 serial converter
```

If the K210 screen is blank and no USB device appears, try another USB-C cable before assuming firmware or board failure.

## K210 Firmware Check

When the K210 is plugged directly into the laptop with a working USB-C cable, its screen should turn on and show the firmware version.

Current module status:

```text
K210 firmware: V1.0.1
Firmware update needed: no
```

The tutorial says only older `V1.0.0` firmware needs updating.

## Flashing MicroPython To ESP32

The ESP32 must run MicroPython for the QD003 Python tutorial path. This replaces the Arduino sketch currently on the ESP32. To return to Arduino later, upload an Arduino sketch again.

Firmware used:

```text
ESP32_GENERIC-20240602-v1.23.0.bin
```

Flash commands:

```bash
uvx esptool --chip esp32 --port /dev/ttyUSB0 erase-flash
uvx esptool --chip esp32 --port /dev/ttyUSB0 --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20240602-v1.23.0.bin
```

Older command spellings also worked, but `esptool` marks them deprecated:

```bash
uvx esptool --chip esp32 --port /dev/ttyUSB0 erase_flash
uvx esptool --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20240602-v1.23.0.bin
```

After flashing, this should work:

```bash
uvx mpremote u0 ls
```

Expected result:

```text
ls :
         139 boot.py
```

## Uploading Files With mpremote

Check the ESP32 serial port:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

For this setup, the ESP32 was:

```text
/dev/ttyUSB0
```

`mpremote` shortcut:

```text
u0 = /dev/ttyUSB0
```

Upload the basic color recognition files:

```bash
uvx mpremote u0 mkdir :/libs
uvx mpremote u0 cp libs/__init__.py :/libs/__init__.py
uvx mpremote u0 cp libs/ACB_Canmv.py :/libs/ACB_Canmv.py
uvx mpremote u0 cp color_recognition.py :/main.py
uvx mpremote u0 reset
```

Open the serial output:

```bash
uvx mpremote u0 repl
```

Exit with:

```text
Ctrl-]
```

## Raw REPL Issue

Before reflashing MicroPython, `mpremote` could connect but filesystem commands failed:

```text
TransportError: could not enter raw repl
```

Reflashing MicroPython fixed this. If this happens again, first try:

```bash
uvx mpremote u0 repl
```

Then press `Ctrl-C` a few times. If that does not work, reflashing MicroPython is the clean fix.

## Wiring K210 To Car Shield

The K210 connector has:

```text
GND, V, TXD, RXD
```

The car shield has an I2C header labeled:

```text
GND, V, SDA, SCL
```

Even though the shield label says I2C, `libs/ACB_Canmv.py` uses UART:

```python
self.SDA = 21
self.SCL = 22
UART(..., rx=Pin(rx_pin), tx=Pin(tx_pin))
```

So in this library:

```text
SDA / GPIO21 = ESP32 RX
SCL / GPIO22 = ESP32 TX
```

Working wiring:

```text
K210 GND -> shield GND
K210 V   -> shield V
K210 TXD -> shield SDA
K210 RXD -> shield SCL
```

The shield has three parallel I2C rows. They appear to be duplicate connections, so any row should work.

Power off before changing wiring.

## Diagnostic Test

`k210_diagnostic.py` is useful before trying full examples.

Upload it as `main.py`:

```bash
uvx mpremote u0 cp k210_diagnostic.py :/main.py
uvx mpremote u0 reset
uvx mpremote u0 repl
```

What it tests:

- changes the K210 RGB light red, green, blue, off
- polls color recognition with `COLOR_INDEX = 0`
- prints a heartbeat if no frame/detection is received

If the RGB light changes, UART from ESP32 to K210 is working.

If the camera screen works but RGB does not change, the K210 has power but UART wiring or pins are still wrong.

## Color Recognition Notes

Tutorial color indexes:

```text
0 = all colors
1 = red
2 = green
3 = blue
```

The original tutorial example uses:

```python
COLOR_INDEX = 3
PIXELS_TH = 200
AREA_TH = 200
```

For easier debugging, use lower thresholds:

```python
COLOR_INDEX = 0
PIXELS_TH = 50
AREA_TH = 50
```

Detection is currently working, but it is not very strong. Better lighting, clear red/green/blue objects, and filling more of the camera view should improve results.

## Current Known State

- K210 powers on with the correct USB-C cable.
- K210 shows firmware `V1.0.1`.
- ESP32 was reflashed with MicroPython `ESP32_GENERIC-20240602-v1.23.0`.
- `mpremote` filesystem upload works after reflashing.
- K210 camera screen works after wiring to the car shield.
- Color detection works, but quality is poor.
