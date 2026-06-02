import json
import math
import time
from dataclasses import dataclass

import serial
from dotenv import load_dotenv
from openai import OpenAI
from dataclasses import dataclass, field


load_dotenv()

client = OpenAI()

MODEL = "gpt-5.4-mini"

PORT = "/dev/ttyUSB0"
BAUD = 115200

X_MIN = 0.0
Y_MIN = 0.0
X_MAX = 8.0
Y_MAX = 8.0

MOVE_UNIT = 1.0
TURN_DEGREES = 10

RIGHT_90_STEPS = 8
LEFT_90_STEPS = 8

VALID_COMMANDS = {"F", "B", "MR", "ML", "CW", "CCW", "TR", "TL", "PD", "PU", "S"}
PLAN_COMMANDS = {"F", "B", "MR", "ML", "CW", "CCW", "TR", "TL", "PD", "PU"}


@dataclass
class CarState:
    x: int = 0
    y: int = 0
    theta: int = 0
    pen_down: bool = False
    drawn_cells: set = field(default_factory=set)


state = CarState()
ser = None
last_response_id = None


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

def grid_cell(x: int, y: int):
    return x, y


def heading_arrow(theta: int) -> str:
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    index = round(normalize_angle(theta) / 45) % 8
    return arrows[index]


def render_grid() -> str:
    return render_grid_for(state)

def get_state_dict():
    return {
        "x": state.x,
        "y": state.y,
        "theta_degrees_clockwise_from_north": state.theta,
        "heading_description": heading_description(state.theta),
        "pen": "down" if state.pen_down else "up",
        "ascii_map": render_grid(),
        "field": {
            "x_min": X_MIN,
            "x_max": X_MAX,
            "y_min": Y_MIN,
            "y_max": Y_MAX,
            "start_position": "bottom-left at (0,0), facing North",
        },
    }

def next_position_for_state(sim_state: CarState, cmd: str):
    theta = sim_state.theta

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

    return sim_state.x + dx, sim_state.y + dy


def simulate_plan(commands: list[str]):
    sim = clone_state()
    errors = []

    for index, raw_cmd in enumerate(commands):
        cmd = raw_cmd.upper().strip()

        if cmd not in PLAN_COMMANDS:
            errors.append(f"Step {index + 1}: invalid command {cmd}")
            break

        if cmd in {"F", "B", "MR", "ML"}:
            new_x, new_y = next_position_for_state(sim, cmd)

            if not inside_bounds(new_x, new_y):
                errors.append(
                    f"Step {index + 1}: {cmd} crosses boundary to ({new_x},{new_y})"
                )
                break

            sim.x = new_x
            sim.y = new_y

            if sim.pen_down:
                sim.drawn_cells.add((sim.x, sim.y))

        elif cmd == "CW":
            sim.theta = normalize_angle(sim.theta + TURN_DEGREES)

        elif cmd == "CCW":
            sim.theta = normalize_angle(sim.theta - TURN_DEGREES)

        elif cmd == "TR":
            sim.theta = normalize_angle(sim.theta + 90)

        elif cmd == "TL":
            sim.theta = normalize_angle(sim.theta - 90)

        elif cmd == "PD":
            sim.pen_down = True
            sim.drawn_cells.add((sim.x, sim.y))

        elif cmd == "PU":
            sim.pen_down = False

    return sim, errors

def preview_plan(commands: list[str]):
    commands = [cmd.upper().strip() for cmd in commands]
    sim, errors = simulate_plan(commands)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "commands": commands,
        "start_state": get_state_dict(),
        "preview_final_state": {
            "x": sim.x,
            "y": sim.y,
            "theta": sim.theta,
            "heading_description": heading_description(sim.theta),
            "pen": "down" if sim.pen_down else "up",
        },
        "preview_ascii_map": render_grid_for(sim),
    }

def execute_plan(commands: list[str]):
    commands = [cmd.upper().strip() for cmd in commands]
    preview = preview_plan(commands)

    if not preview["ok"]:
        return {
            "ok": False,
            "error": "Plan failed validation. Nothing executed.",
            "preview": preview,
        }

    results = []

    for cmd in commands:
        result = execute_command(cmd)
        results.append({"command": cmd, "result": result})

        if not result.get("ok"):
            execute_command("S")
            return {
                "ok": False,
                "error": f"Execution stopped at command {cmd}",
                "results": results,
                "state": get_state_dict(),
            }

    return {
        "ok": True,
        "message": "Plan executed successfully.",
        "commands": commands,
        "results": results,
        "state": get_state_dict(),
    }

def print_state():
    s = get_state_dict()
    print(
        f"STATE: x={s['x']}, y={s['y']}, "
        f"theta={s['theta_degrees_clockwise_from_north']}° "
        f"[{s['heading_description']}], pen={s['pen']}"
    )
    print(render_grid())


def connect():
    global ser
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print("Connected")
    print_state()


def send_raw(cmd: str, timeout_s: float = 5.0) -> str:
    print(f"EXECUTING: {cmd}")
    ser.write((cmd + "\n").encode())

    deadline = time.time() + timeout_s

    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        print(f"CAR: {cmd} -> {line}")

        if line in {"DONE", "PEN_DOWN", "PEN_UP", "STOPPED", "UNKNOWN_COMMAND"}:
            return line

    print(f"CAR: {cmd} -> TIMEOUT")
    return "TIMEOUT"


def direction_delta(theta_deg: int):
    theta = normalize_angle(theta_deg)

    # Snap heading to nearest 45° direction
    bucket = round(theta / 45) % 8

    directions = {
        0: (0, 1),    # N
        1: (1, 1),    # NE
        2: (1, 0),    # E
        3: (1, -1),   # SE
        4: (0, -1),   # S
        5: (-1, -1),  # SW
        6: (-1, 0),   # W
        7: (-1, 1),   # NW
    }

    return directions[bucket]


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
    return X_MIN - eps <= x <= X_MAX + eps and Y_MIN - eps <= y <= Y_MAX + eps


def execute_command(command: str):
    command = command.upper().strip()

    allowed = {"F", "B", "MR", "ML", "CW", "CCW", "TR", "TL", "PD", "PU", "S"}

    if command not in allowed:
        return {
            "ok": False,
            "error": f"Invalid command: {command}",
            "state": get_state_dict(),
        }

    if command in {"F", "B", "MR", "ML"}:
        new_x, new_y = next_position_for(command)

        if not inside_bounds(new_x, new_y):
            return {
                "ok": False,
                "error": f"Boundary blocked. Would move to x={new_x}, y={new_y}",
                "state": get_state_dict(),
            }

        result = send_raw(command)

        if result == "DONE":
            state.x = new_x
            state.y = new_y
            if state.pen_down:
                state.drawn_cells.add(grid_cell(state.x, state.y))

        return {
            "ok": result == "DONE",
            "car_result": result,
            "state": get_state_dict(),
        }

    if command == "CW":
        result = send_raw("CW")

        if result == "DONE":
            state.theta = normalize_angle(state.theta + TURN_DEGREES)

        return {
            "ok": result == "DONE",
            "car_result": result,
            "state": get_state_dict(),
        }

    if command == "CCW":
        result = send_raw("CCW")

        if result == "DONE":
            state.theta = normalize_angle(state.theta - TURN_DEGREES)

        return {
            "ok": result == "DONE",
            "car_result": result,
            "state": get_state_dict(),
        }

    if command == "TR":
        for _ in range(RIGHT_90_STEPS):
            result = send_raw("CW")
            if result != "DONE":
                return {"ok": False, "car_result": result, "state": get_state_dict()}
            state.theta = normalize_angle(state.theta + TURN_DEGREES)

        return {"ok": True, "car_result": "DONE", "state": get_state_dict()}

    if command == "TL":
        for _ in range(LEFT_90_STEPS):
            result = send_raw("CCW")
            if result != "DONE":
                return {"ok": False, "car_result": result, "state": get_state_dict()}
            state.theta = normalize_angle(state.theta - TURN_DEGREES)

        return {"ok": True, "car_result": "DONE", "state": get_state_dict()}

    if command == "PD":
        result = send_raw("PD")
        if result == "PEN_DOWN":
            state.pen_down = True
            state.drawn_cells.add(grid_cell(state.x, state.y))

        return {"ok": result == "PEN_DOWN", "car_result": result, "state": get_state_dict()}

    if command == "PU":
        result = send_raw("PU")
        if result == "PEN_UP":
            state.pen_down = False

        return {"ok": result == "PEN_UP", "car_result": result, "state": get_state_dict()}

    if command == "S":
        result = send_raw("S")
        return {"ok": result == "STOPPED", "car_result": result, "state": get_state_dict()}


def reset_virtual_state():
    state.x = 0
    state.y = 0
    state.theta = 0
    state.pen_down = False
    state.drawn_cells.clear()

    return {
        "ok": True,
        "message": "Virtual state reset. Physically place car at bottom-left facing North.",
        "state": get_state_dict(),
    }


tools = [
    {
        "type": "function",
        "name": "get_state",
        "description": "Get the current estimated car state, field rules, and ASCII map.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "preview_plan",
        "description": "Preview a full command plan without moving the real car. Use this before execute_plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["F", "B", "MR", "ML", "CW", "CCW", "TR", "TL", "PD", "PU"],
                    },
                }
            },
            "required": ["commands"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "execute_plan",
        "description": "Execute a full previously-previewed command plan on the real car.",
        "parameters": {
            "type": "object",
            "properties": {
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["F", "B", "MR", "ML", "CW", "CCW", "TR", "TL", "PD", "PU"],
                    },
                }
            },
            "required": ["commands"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "reset_virtual_state",
        "description": "Reset the virtual position to bottom-left (0,0), facing North.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def call_local_tool(name: str, args: dict):
    if name == "get_state":
        return get_state_dict()

    if name == "preview_plan":
        return preview_plan(args["commands"])

    if name == "execute_plan":
        return execute_plan(args["commands"])

    if name == "reset_virtual_state":
        return reset_virtual_state()

    return {"ok": False, "error": f"Unknown tool: {name}"}

def clone_state():
    return CarState(
        x=state.x,
        y=state.y,
        theta=state.theta,
        pen_down=state.pen_down,
        drawn_cells=set(state.drawn_cells),
    )

def render_grid_for(sim_state: CarState) -> str:
    car_x, car_y = sim_state.x, sim_state.y

    lines = []
    lines.append("      X →  0 1 2 3 4 5 6 7 8")
    lines.append("Y")
    lines.append("↑")

    for y in range(int(Y_MAX), int(Y_MIN) - 1, -1):
        row = []

        for x in range(int(X_MIN), int(X_MAX) + 1):
            if x == car_x and y == car_y:
                row.append("C")
            elif (x, y) in sim_state.drawn_cells:
                row.append("*")
            elif x == 0 and y == 0:
                row.append("S")
            else:
                row.append(".")

        lines.append(f"{y:>2} |        " + " ".join(row))

    lines.append("             0 1 2 3 4 5 6 7 8")
    lines.append("Legend: S=start, C=car, *=drawn trail")
    return "\n".join(lines)

def normalize_commands(commands: list[str]) -> list[str]:
    return [cmd.upper().strip() for cmd in commands]

SYSTEM_PROMPT = """
You control a real ESP32 smart car through Python tools.

The car is on a physical table, but Python tracks a virtual 9x9 grid.

GRID:
- x is 0 to 8.
- y is 0 to 8.
- (0,0) is bottom-left.
- +X is right/East.
- +Y is up/North.
- The car starts at (0,0), facing North.
- The car always occupies one integer cell.
- Never move outside the grid.

HEADING:
- theta is clockwise from North.
- 0° = North.
- 90° = East.
- 180° = South.
- 270° = West.

COMMANDS:
- F: move one cell toward the car nose.
- B: move one cell backward.
- MR: strafe one cell right.
- ML: strafe one cell left.
- CW: turn 10° clockwise.
- CCW: turn 10° counterclockwise.
- TR: turn about 90° right.
- TL: turn about 90° left.
- PD: pen down, LEDs on.
- PU: pen up, LEDs off.

TOOLS:
- get_state: check current state and map.
- preview_plan: simulate a full command list without moving the car.
- execute_plan: execute a validated command list on the real car.
- reset_virtual_state: reset virtual state to (0,0), facing North.

RULES:
- Always call get_state first.
- For drawing tasks, generate the full command list first.
- Always call preview_plan before execute_plan.
- Only call execute_plan if the preview matches the user request.
- Do not execute drawing commands one by one.
- For simple shapes, prefer F/B/MR/ML. Avoid turns unless needed.
- Center drawings when possible.
- Avoid the outer boundary unless the user asks.
- Use visible shapes, usually 3 to 5 cells wide/tall.
- Use PU to move to the start point, then PD to draw, then PU at the end.
- Be simple, safe, and correct.
- You may call preview_plan multiple times, but you may call execute_plan only once per user request.
- After execute_plan, do not call any more tools. Summarize the result.
"""


def run_agent(user_goal: str):
    global last_response_id

    previewed_commands = None
    executed_plan = False

    create_kwargs = {
        "model": MODEL,
        "instructions": SYSTEM_PROMPT,
        "reasoning": {"effort": "high"},
        "input": [{"role": "user", "content": user_goal}],
        "tools": tools,
    }

    if last_response_id is not None:
        create_kwargs["previous_response_id"] = last_response_id

    response = client.responses.create(**create_kwargs)

    while True:
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            print(response.output_text)
            last_response_id = response.id
            return

        tool_outputs = []
        pending_preview = None

        for call in tool_calls:
            args = json.loads(call.arguments or "{}")

            if call.name == "preview_plan":
                commands = normalize_commands(args["commands"])
                result = preview_plan(commands)

                if result["ok"]:
                    pending_preview = commands

            elif call.name == "execute_plan":
                commands = normalize_commands(args["commands"])

                if executed_plan:
                    result = {
                        "ok": False,
                        "error": "execute_plan already ran for this user goal. No more execution allowed.",
                        "state": get_state_dict(),
                    }

                elif previewed_commands is None:
                    result = {
                        "ok": False,
                        "error": "You must call preview_plan first, wait for the preview result, then call execute_plan.",
                        "state": get_state_dict(),
                    }

                elif commands != previewed_commands:
                    result = {
                        "ok": False,
                        "error": "execute_plan commands do not match the last successful preview_plan commands.",
                        "previewed_commands": previewed_commands,
                        "attempted_commands": commands,
                        "state": get_state_dict(),
                    }

                else:
                    result = execute_plan(commands)
                    executed_plan = True

            else:
                result = call_local_tool(call.name, args)

            print_state()

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result),
                }
            )

        if pending_preview is not None:
            previewed_commands = pending_preview

        if executed_plan:
            final = client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                reasoning={"effort": "medium"},
                previous_response_id=response.id,
                input=tool_outputs,
            )

            print(final.output_text)
            last_response_id = final.id
            return

        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            reasoning={"effort": "high"},
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools,
        )


def main():
    connect()

    print("Agent ready.")
    print("Try: draw a small L shape")
    print("Type quit to stop.")

    while True:
        goal = input("\nGoal> ").strip()

        if goal.lower() in {"quit", "exit"}:
            execute_command("S")
            break

        if goal.lower() == "state":
            print_state()
            continue

        if goal.lower() == "reset":
            print(reset_virtual_state())
            continue

        run_agent(goal)

    ser.close()


if __name__ == "__main__":
    main()