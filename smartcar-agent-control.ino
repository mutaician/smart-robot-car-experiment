#include <vehicle.h>
#include <ESP32Servo.h>

vehicle myCar;
Servo myServo;

const int LEFT_LED = 12;
const int RIGHT_LED = 2;

const int SERVO_PIN = 27;
const int SERVO_CENTER = 110;

const int MOVE_MS = 200;
const int MOVE_SPEED = 150;

const int TURN_MS = 100;
const int TURN_SPEED = 200;

void stopCar() {
  myCar.Move(Stop, 0);
}

void moveOnce(int direction) {
  myCar.Move(direction, MOVE_SPEED);
  delay(MOVE_MS);
  stopCar();
  Serial.println("DONE");
}

void turnOnce(int direction) {
  myCar.Move(direction, TURN_SPEED);
  delay(TURN_MS);
  stopCar();
  Serial.println("DONE");
}

void penDown() {
  digitalWrite(LEFT_LED, HIGH);
  digitalWrite(RIGHT_LED, HIGH);
  Serial.println("PEN_DOWN");
}

void penUp() {
  digitalWrite(LEFT_LED, LOW);
  digitalWrite(RIGHT_LED, LOW);
  Serial.println("PEN_UP");
}

void setup() {
  Serial.begin(115200);

  myCar.Init();

  pinMode(LEFT_LED, OUTPUT);
  pinMode(RIGHT_LED, OUTPUT);

  myServo.attach(SERVO_PIN);
  myServo.write(SERVO_CENTER);

  stopCar();
  penUp();

  Serial.println("READY");
  Serial.println("Commands: F B ML MR CW CCW PD PU S");
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "F") {
    moveOnce(Forward);
  }
  else if (cmd == "B") {
    moveOnce(Backward);
  }
  else if (cmd == "ML") {
    moveOnce(Move_Left);
  }
  else if (cmd == "MR") {
    moveOnce(Move_Right);
  }
  else if (cmd == "CW") {
    turnOnce(Clockwise);
  }
  else if (cmd == "CCW") {
    turnOnce(Contrarotate);
  }
  else if (cmd == "PD") {
    penDown();
  }
  else if (cmd == "PU") {
    penUp();
  }
  else if (cmd == "S") {
    stopCar();
    Serial.println("STOPPED");
  }
  else {
    Serial.println("UNKNOWN_COMMAND");
  }
}