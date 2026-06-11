/*
 Project 06 Motor drive and speed regulation
 Motor moves forward, backward, left and right
*/ 
const int left_ctrl = 4;//define the direction control pin(D4) of the left motor
const int left_pwm = 6;// define the speed control pin(D6) of the left motor
const int right_ctrl = 2;//define the direction control pin(D2) of the right motor
const int right_pwm = 5;//define the speed control pin(D5) of the right motor
const int speed = 140;

void setup()
{
  pinMode(left_ctrl,OUTPUT);//Set the direction control pin of the left motor to OUTPUT
  pinMode(left_pwm,OUTPUT);//Set the PWM control speed of the left motor to OUTPUT
  pinMode(right_ctrl,OUTPUT);//Set the direction control pin of the right motor to OUTPUT
  pinMode(right_pwm,OUTPUT);//Set the PWM control speed of the right motor to OUTPUT
}

void loop()
{ 
  //front
  digitalWrite(left_ctrl,LOW); //Set direction control pins of the left motor to LOW
  analogWrite(left_pwm,speed); //Set the PWM control speed of the left motor to 200
  digitalWrite(right_ctrl,LOW); //set control pins of the right motor to LOW
  analogWrite(right_pwm,speed); //Set the PWM control speed of the right motor to 200
  delay(2000);//delay in 2s
  
  //back
  digitalWrite(left_ctrl,HIGH); //set control pins of the left motor to HIGH
  analogWrite(left_pwm,speed); //Set the PWM control speed of the left motor to 50
  digitalWrite(right_ctrl,HIGH); //Set direction control pins of the right motor to HIGH
  analogWrite(right_pwm,speed); //Set the PWM control speed of the right motor to 50
  delay(2000);//delay in 2s
  
  // //left
  // digitalWrite(left_ctrl,HIGH); //set control pins of the left motor to HIGH
  // analogWrite(left_pwm,speed); //Set the PWM control speed of the left motor to 200
  // digitalWrite(right_ctrl,LOW); //set control pins of the right motor to LOW
  // analogWrite(right_pwm,speed); //Set the PWM control speed of the right motor to 200
  // delay(2000);//delay in 2s
  
  // //right
  // digitalWrite(left_ctrl,LOW); //Set direction control pins of the left motor to LOW
  // analogWrite(left_pwm,speed); //Set the PWM control speed of the left motor to 200
  // digitalWrite(right_ctrl,HIGH); //Set direction control pins of the right motor to HIGH
  // analogWrite(right_pwm,speed); //Set the PWM control speed of the right motor to 200
  // delay(2000);//delay in 2s
  
  //stop
  digitalWrite(left_ctrl,LOW);//Set direction control pins of the left motor to LOW
  analogWrite(left_pwm,0);//Set the PWM control speed of the left motor to 0
  digitalWrite(right_ctrl,LOW);//set control pins of the right motor to LOW
  analogWrite(right_pwm,0);//set Set the PWM control speed of the right motor to 0
  delay(2000);//delay in 2s
}