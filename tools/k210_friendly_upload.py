import argparse
import time

import serial


def wait_for_prompt(ser, timeout=5):
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            if b">>> " in buf or b"... " in buf:
                return buf
    return buf


def send_line(ser, line):
    ser.write(line.encode() + b"\r\n")
    ser.flush()
    return wait_for_prompt(ser)


def main():
    parser = argparse.ArgumentParser(description="Upload a small file to CanMV/K210 via friendly REPL.")
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--chunk-size", type=int, default=96)
    parser.add_argument("--verify", action="store_true", help="Print the uploaded file after writing.")
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as f:
        text = f.read()

    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        time.sleep(0.5)
        for _ in range(4):
            ser.write(b"\x03")
            ser.flush()
            time.sleep(0.2)
        startup = wait_for_prompt(ser)
        if b">>> " not in startup:
            print(startup.decode(errors="ignore"), end="")
            print("Warning: did not see a clean REPL prompt before upload.")

        print(send_line(ser, "f = open(%r, 'w')" % args.target).decode(errors="ignore"), end="")

        for i in range(0, len(text), args.chunk_size):
            chunk = text[i : i + args.chunk_size]
            print(send_line(ser, "f.write(%r)" % chunk).decode(errors="ignore"), end="")

        print(send_line(ser, "f.close()").decode(errors="ignore"), end="")
        if args.verify:
            print(send_line(ser, "print(open(%r).read())" % args.target).decode(errors="ignore"), end="")


if __name__ == "__main__":
    main()
