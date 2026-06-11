/*
Project 07.2: follow me
Car follows the object
*/ 
const int left_ctrl = 4;//define direction control pins of the left motor as D4
const int left_pwm = 6;//define speed control pins of the left motor as D6
const int right_ctrl = 2;//define the direction control pin of the right motor D2
const int right_pwm = 5;//define the speed control pin of the right motor D5
#include "SR04.h" //define the ultrasonic module function library
#define TRIG_PIN 8// define signals input of the ultrasonic asD8
#define ECHO_PIN 7//define the signal output of the ultrasonic sensor as D7
SR04 sr04 = SR04(ECHO_PIN,TRIG_PIN);
long distance;
const int servopin = 9;//define the pin of the servo asD9
int myangle;
int pulsewidth;

void setup() {
  Serial.begin(9600);
  pinMode(left_ctrl,OUTPUT);//Set the direction control pin of the left motor to OUTPUT
  pinMode(left_pwm,OUTPUT);//Set the PWM control speed of the left motor to OUTPUT
  pinMode(right_ctrl,OUTPUT);//Set the direction control pin of the right motor to OUTPUT
  pinMode(right_pwm,OUTPUT);//Set the PWM control speed of the right motor to OUTPUT
  pinMode(TRIG_PIN,OUTPUT);//Set TRIG_PIN to OUTPUT
  pinMode(ECHO_PIN,INPUT);//Set ECHO_PIN to INPUT
  servopulse(servopin,90);//set the initial angle to 90
  delay(300);
}

void loop() {
  distance = sr04.Distance();//the distance detected by the ultrasonic sensor
  Serial.println(distance);
  // if(distance<8)//if the distance is less than 8
  // {
  //   back();//go back
  // }
  // else if((distance>=8)&&(distance<13))//if 8≤distance<13
  // {
  //   Stop();//stop
  // }
  // else if((distance>=13)&&(distance<35))//if 13≤distance<35
  // {
  //   front();//follow
  // }
  // else//if above conditions are not met
  // {
  //   Stop();//stop
  // }
}

void servopulse(int servopin,int myangle)//angles the servo rotate
{
  for(int i=0; i<20; i++)
  {
    pulsewidth = (myangle*11)+500;
    digitalWrite(servopin,HIGH);
    delayMicroseconds(pulsewidth);
    digitalWrite(servopin,LOW);
    delay(20-pulsewidth/1000);
  }  
}

void front()//define the state of going forward
{
  digitalWrite(left_ctrl,LOW); //Set direction control pins of the left motor to LOW
  analogWrite(left_pwm,200); //Set the PWM control speed of the left motor to 200
  digitalWrite(right_ctrl,LOW); //set control pins of the right motor to LOW
  analogWrite(right_pwm,200); //Set the PWM control speed of the right motor to 200
}
void back()//define the state of going back
{
  digitalWrite(left_ctrl,HIGH); //set control pins of the left motor to HIGH
  analogWrite(left_pwm,50); //Set the PWM control speed of the left motor to 50
  digitalWrite(right_ctrl,HIGH); //Set direction control pins of the right motor to HIGH
  analogWrite(right_pwm,50); //Set the PWM control speed of the right motor to 50
}
void Stop()//define the state of stop
{
  digitalWrite(left_ctrl,LOW);//Set direction control pins of the left motor to LOW
  analogWrite(left_pwm,0);//set the PWM control speed of the left motor to 0
  digitalWrite(right_ctrl,LOW);//set control pins of the right motor to LOW
  analogWrite(right_pwm,0);//set the PWM control speed of the right motor to 0
}