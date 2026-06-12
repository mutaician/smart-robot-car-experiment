/*
Project 09.1:Read Photosensor Value
*/
int sensorPin = A6;    // select the input pin for the photocell
int sensorPinr = A7;
int sensorValue = 0; 
int sensorvaluer = 0; // variable to store the value coming from the sensor
void setup() {
Serial.begin(9600);
}
void loop() {
sensorValue = analogRead(sensorPin);  // read the value from the sensor:
sensorvaluer = analogRead(sensorPinr);
Serial.print("left photoresistor: ");
Serial.println(sensorValue);  //Serial port prints the value of photoresistor
Serial.print("right photoresistor: ");
Serial.println(sensorvaluer);
delay(500);
}