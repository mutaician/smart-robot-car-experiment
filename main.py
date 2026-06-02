import math
import time
from dataclasses import dataclass

import serial


PORT = "/dev/ttyUSB0"
BAUD = 115200

X_MIN = 0.0
Y_MIN = 0.0
X_MAX = 8.0
Y_MAX = 8.0

MOVE_UNIT = 1.0

TURN_DEGREES = 10
RIGHT_90_STEPS = 9
LEFT_90_STEPS = 9


@dataclass
class CarState:
    x: float = 0.0
    y: float = 0.0
    theta: int = 0  # degrees clockwise from North
    pen_down: bool = False


state = CarState()


def normalize_angle(theta: int) -> int:
    return theta % 360


def clean_float(value: float) -> float:
    if abs(value) < 1e-9:
        return 0.0
    return round(value, 3)


def heading_description(theta: int) -> str:
    theta = normalize_angle(theta)

    if theta == 0:
        return "N"
    if theta == 90:
        return "E"
    if theta == 180:
        return "S"
    if theta == 270:
        return "W"

    if 0 < theta < 90:
        return f"between N and E, {theta}° clockwise from N"
    if 90 < theta < 180:
        return f"between E and S, {theta - 90}° clockwise from E"
    if 180 < theta < 270:
        return f"between S and W, {theta - 180}° clockwise from S"

    return f"between W and N, {theta - 270}° clockwise from W"


def print_state():
    print(
        f"STATE: x={clean_float(state.x)}, "
        f"y={clean_float(state.y)}, "
        f"theta={state.theta}° [{heading_description(state.theta)}], "
        f"pen={'down' if state.pen_down else 'up'}"
    )


def connect():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print("Connected")
    return ser


def send_raw(ser, cmd: str, timeout_s: float = 5.0) -> str:
    ser.write((cmd + "\n").encode())

    deadline = time.time() + timeout_s

    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        print("CAR:", line)

        if line in {"DONE", "PEN_DOWN", "PEN_UP", "STOPPED", "UNKNOWN_COMMAND"}:
            return line

    print("CAR: TIMEOUT")
    return "TIMEOUT"


def direction_delta(theta_deg: int, unit: float = MOVE_UNIT):
    rad = math.radians(theta_deg)
    dx = math.sin(rad) * unit
    dy = math.cos(rad) * unit
    return dx, dy


def next_position_for(cmd: str):
    theta = state.theta

    if cmd == "F":
        dx, dy = direction_delta(theta)
    elif cmd == "B":
        dx, dy = direction_delta(theta + 180)
    elif cmd == "MR":
        dx, dy = direction_delta(theta + 90)
    elif cmd == "ML":
        dx, dy = direction_delta(theta - 90)
    else:
        raise ValueError(f"Not a movement command: {cmd}")

    return state.x + dx, state.y + dy


def inside_bounds(x: float, y: float) -> bool:
    eps = 1e-6
    return (
        X_MIN - eps <= x <= X_MAX + eps
        and Y_MIN - eps <= y <= Y_MAX + eps
    )


def apply_movement(ser, cmd: str):
    new_x, new_y = next_position_for(cmd)

    if not inside_bounds(new_x, new_y):
        print(f"BLOCKED: boundary would be crossed -> x={clean_float(new_x)}, y={clean_float(new_y)}")
        print_state()
        return

    result = send_raw(ser, cmd)

    if result == "DONE":
        state.x = clean_float(new_x)
        state.y = clean_float(new_y)

    print_state()


def apply_turn(ser, cmd: str):
    result = send_raw(ser, cmd)

    if result == "DONE":
        if cmd == "CW":
            state.theta = normalize_angle(state.theta + TURN_DEGREES)
        elif cmd == "CCW":
            state.theta = normalize_angle(state.theta - TURN_DEGREES)

    print_state()


def turn_right_90(ser):
    for _ in range(RIGHT_90_STEPS):
        result = send_raw(ser, "CW")

        if result != "DONE":
            break

        state.theta = normalize_angle(state.theta + TURN_DEGREES)

    print_state()


def turn_left_90(ser):
    for _ in range(LEFT_90_STEPS):
        result = send_raw(ser, "CCW")

        if result != "DONE":
            break

        state.theta = normalize_angle(state.theta - TURN_DEGREES)

    print_state()


def pen_down(ser):
    result = send_raw(ser, "PD")

    if result == "PEN_DOWN":
        state.pen_down = True

    print_state()


def pen_up(ser):
    result = send_raw(ser, "PU")

    if result == "PEN_UP":
        state.pen_down = False

    print_state()


def reset_virtual_state():
    state.x = 0.0
    state.y = 0.0
    state.theta = 0
    state.pen_down = False
    print("Virtual state reset. Physically place car at bottom-left facing North.")
    print_state()


def handle_command(ser, cmd: str):
    cmd = cmd.upper().strip()

    if cmd in {"F", "B", "MR", "ML"}:
        apply_movement(ser, cmd)

    elif cmd in {"CW", "CCW"}:
        apply_turn(ser, cmd)

    elif cmd == "TR":
        turn_right_90(ser)

    elif cmd == "TL":
        turn_left_90(ser)

    elif cmd == "PD":
        pen_down(ser)

    elif cmd == "PU":
        pen_up(ser)

    elif cmd == "S":
        send_raw(ser, "S")
        print_state()

    elif cmd == "STATE":
        print_state()

    elif cmd == "RESET":
        reset_virtual_state()

    else:
        print("Unknown command")


def main():
    ser = connect()

    print_state()
    print("Commands: f b mr ml cw ccw tr tl pd pu s state reset quit")

    while True:
        cmd = input("> ").strip()

        if not cmd:
            continue

        if cmd.lower() == "quit":
            send_raw(ser, "S")
            break

        handle_command(ser, cmd)

    ser.close()


if __name__ == "__main__":
    main()