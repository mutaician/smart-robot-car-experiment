# K210 YOLO / Laptop Detection Notes

These notes document the YOLO experiment with the ACEBOTT QD003 K210 module.

The original idea was to run YOLO directly on the K210. The working approach we reached was different:

```text
K210 camera -> tiny RGB frame over USB serial -> laptop YOLO -> laptop detection window
```

This avoids flashing the K210 firmware.

## What We Learned

The ACEBOTT `canm_V1.0.1.bin` firmware is based on CanMV/MicroPython.

The K210 REPL shows:

```text
MicroPython v1.0.5-4-g42c54b5-dirty on 2025-06-18; CanMV_Board with kendryte-k210
```

The firmware binary contains strings for:

```text
CanMV
KPU
sensor
lcd
load_kmodel
ObjectDetection.py
TrafficCard.py
face_recognition.py
color_recognition.py
feature_learning.py
main_app.py
```

So the ACEBOTT firmware is not a completely opaque native-only firmware. It includes CanMV runtime support and frozen/bundled ACEBOTT modules.

## ACEBOTT Built-In Flow

The normal ACEBOTT image-recognition flow is:

```text
ESP32 sends mode command -> K210 runs built-in recognition -> ESP32 receives box + label
```

For image recognition, ESP32 sends:

```text
[5, 13, 10]
```

The K210 returns packets like:

```text
[15, 0, 116, 15, 0, 60, 120, 0, 146, 75, 66, 111, 116, 116, 108, 101]
```

Parsed:

```text
payload length = 15
x = 116
y = 15
w = 60
h = 120
cx = 146
cy = 75
label = Bottle
```

This confirms the original `image-recognition.py` receives recognition results, not raw frames.

## K210 REPL Access

Plug the USB cable directly into the K210 module, not the ESP32.

Connect:

```bash
uvx mpremote connect /dev/ttyUSB0 repl
```

If the default ACEBOTT app is still running, press `Ctrl-C`.

Useful REPL checks:

```python
import os
print(os.getcwd())
print(os.listdir('/flash'))
print(open('/flash/main.py').read())
print(open('/flash/config.json').read())
```

The default `/flash/main.py` was:

```python
import main_app
```

To disable the default ACEBOTT startup:

```python
f = open("main.py", "w")
f.write("# disabled default ACEBOTT app\n")
f.close()
```

To restore ACEBOTT startup:

```python
f = open("main.py", "w")
f.write("import main_app\n")
f.close()
```

This edits only `/flash/main.py`; it does not flash firmware.

## mpremote Limitation

Normal REPL works, but `mpremote cp` / `mpremote run` failed because this CanMV build would not enter raw REPL:

```text
TransportError: could not enter raw repl
```

Improvised workaround:

```text
tools/k210_friendly_upload.py
```

This uploads small files by typing `open(...).write(...)` commands into the friendly REPL.

Example:

```bash
uv run python tools/k210_friendly_upload.py k210_send_tiny_frame.py main.py --port /dev/ttyUSB0 --verify
```

Then reset/replug the K210 so `main.py` runs.

## Custom Camera Script

We first tested a simple custom K210 script:

```text
cover.main.py
```

It proved:

```text
custom K210 code can run
sensor works
lcd works
no firmware flashing needed
```

The K210 LCD orientation and raw streamed frame orientation can differ. The LCD can look upright while laptop-decoded frames need rotation.

## Tiny Frame Streaming

The working stream sender is:

```text
k210_send_tiny_frame.py
```

It does:

```text
K210 camera snapshot
display raw camera image on K210 LCD
resize to 80x60
encode RGB565 frame as base64
print as a serial line
```

Frame protocol:

```text
FRAME RGB565 80 60 <base64-payload>
```

The laptop receiver is:

```text
vision/read_k210_tiny_frame.py
```

Run:

```bash
uv run python vision/read_k210_tiny_frame.py --port /dev/ttyUSB0
```

If orientation is wrong:

```bash
uv run python vision/read_k210_tiny_frame.py --port /dev/ttyUSB0 --rotate none
```

## Laptop YOLO

The YOLO laptop-side script is:

```text
vision/k210_yolo_roundtrip.py
```

Despite the filename, the current working version is one-way:

```text
K210 -> laptop frames -> laptop YOLO visualization
```

Run:

```bash
uv run python vision/k210_yolo_roundtrip.py --port /dev/ttyUSB0 --model yolo11n.pt
```

Installed dependencies:

```text
ultralytics 8.4.60
torch 2.12.0+cu130
CUDA available: True
```

The first run may download `yolo11n.pt`.

## Attempted K210 Visualization

We tried sending laptop detections back to K210 so the K210 LCD could draw boxes.

That failed because this CanMV firmware does not support polling `sys.stdin` with `select`:

```text
OSError: stream operation not supported
```

So the current working path visualizes YOLO boxes on the laptop, while the K210 LCD shows the raw camera feed.

## Latency And Quality

Latency is high because frames are sent as base64 text over USB serial at `115200` baud.

Approximate raw frame sizes before base64 overhead:

```text
80x60 grayscale       = 4.8 KB
80x60 RGB565 color    = 9.6 KB
160x120 RGB565 color  = 38.4 KB
320x240 RGB565 color  = 153.6 KB
```

Base64 adds about 33 percent overhead.

So full QVGA color over serial is not practical. The useful range is:

```text
80x60 color: works, high latency
120x90 color: possible but slower
160x120 color: likely very slow
320x240 color: not practical over this serial method
```

The laptop model can use RGB data, but the serial link is the bottleneck.

## Direct K210 YOLO Idea

Running YOLO directly on the K210 is still possible in theory, but it needs a K210-compatible `.kmodel`, not a normal Ultralytics `.pt` file.

The original demo script for this idea is:

```text
k210_yolo_demo.py
```

It expects something like:

```text
/sd/voc20_detect.kmodel
```

However, the SD card was not detected in this setup, and flashing models/firmware was considered risky. This path is paused.

## Current Status

Achieved:

```text
K210 firmware inspected enough to confirm CanMV/MicroPython base
K210 REPL access works
default ACEBOTT startup can be disabled/restored via /flash/main.py
custom K210 camera/display script works
small RGB565 frames can be streamed to laptop
laptop can decode K210 frames
Ultralytics YOLO runs on laptop GPU
YOLO detections appear in laptop window
```

Current limitation:

```text
serial streaming latency is high
K210 LCD does not yet receive/draw laptop detections
full-quality video is not practical over the current serial-text protocol
```
