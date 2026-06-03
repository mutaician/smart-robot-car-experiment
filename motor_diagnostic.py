from libs import vehicle
import time


print("Starting motor diagnostic...")
print("Make sure the motor battery is connected.")
print("The car will move in short bursts, then stop.")

car = vehicle.ACB_Vehicle()


def run_step(name, direction, speed=150, duration_ms=500):
    print("Step:", name, "speed:", speed, "duration_ms:", duration_ms)
    car.Move(direction, speed)
    time.sleep_ms(duration_ms)
    car.Move(car.Stop, 0)
    time.sleep_ms(600)


try:
    car.Move(car.Stop, 0)
    time.sleep_ms(500)

    run_step("forward", car.Forward)
    run_step("backward", car.Backward)
    # run_step("move left", car.Move_Left)
    # run_step("move right", car.Move_Right)
    # run_step("clockwise", car.Clockwise)
    # run_step("counter-clockwise", car.Contrarotate)

    print("Motor diagnostic complete.")
finally:
    car.Move(car.Stop, 0)
    print("Stopped.")
