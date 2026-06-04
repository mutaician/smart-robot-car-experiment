from machine import Pin, PWM, Timer, ADC
import network
import socket
import select
import time
import libs.servo
import libs.ultrasonic
from libs import ACB_Canmv
import libs.vehicle

LED_Module1 = 2
LED_Module2 = 12
Shoot_PIN = 32
buzzer = 33
FIXED_SERVO_PIN = 25
TURN_SERVO_PIN = 26
left_track_sensor = 35
center_track_sensor = 36
right_track_sensor = 39
Trig_PIN = 13
Echo_PIN = 14

cam = ACB_Canmv.ACB_Canmv()
cam.Yservo_PIN = 26

cam.init(cam.SDA, cam.SCL)

servo_fixed = libs.servo.Servo()

Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

car = libs.vehicle.ACB_Vehicle()  # Creating a car object (auto init inside)

adc1 = ADC(left_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc1.width(ADC.WIDTH_12BIT)
adc1.atten(ADC.ATTN_11DB)
adc2 = ADC(right_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc2.width(ADC.WIDTH_12BIT)
adc2.atten(ADC.ATTN_11DB)
adc3 = ADC(center_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc3.width(ADC.WIDTH_12BIT)
adc3.atten(ADC.ATTN_11DB)

LED1 = None
LED2 = None

speeds = 190
Black_Line = 2000
Off_Road = 4000
data = None
C3 = 131
D3 = 147
E3 = 165
F3 = 175
G3 = 196
A3 = 221
B3 = 248

C4 = 262
D4 = 294
E4 = 330
F4 = 350
G4 = 393
A4 = 441
B4 = 495

C5 = 525
D5 = 589
E5 = 661
F5 = 700
G5 = 786
A5 = 882
B5 = 990

N = 0

r = 0
g = 0
b = 0

# Define tunes
# little star
tune0 = [C4, N, C4, G4, N, G4, A4, N, A4, G4, N, F4, N, F4, E4, N, E4, D4, N, D4, C4]
durt0 = [0.99, 0.01, 1, 0.99, 0.01, 1, 0.99, 0.01, 1, 1.95, 0.05, 0.99, 0.01, 1, 0.99, 0.01, 1, 0.99, 0.01, 1, 2]

# jingle bell
tune1 = [E4, N, E4, N, E4, N, E4, N, E4, N, E4, N, E4, G4, C4, D4, E4]
durt1 = [0.49, 0.01, 0.49, 0.01, 0.99, 0.01, 0.49, 0.01, 0.49, 0.01, 0.99, 0.01, 0.5, 0.5, 0.75, 0.25, 1, 2]

# happy new year
tune2 = [C5, N, C5, N, C5, G4, E5, N, E5, N, E5, C5, N, C5, E5, G5, N, G5, F5, E5, D5, N]
durt2 = [0.49, 0.01, 0.49, 0.01, 1, 1, 0.49, 0.01, 0.49, 0.01, 1, 0.99, 0.01, 0.5, 0.5, 0.99, 0.01, 1, 0.5, 0.5, 1, 1]

# have a farm
tune3 = [C4, N, C4, N, C4, G3, A3, N, A3, G3, E4, N, E4, D4, N, D4, C4]
durt3 = [0.99, 0.01, 0.99, 0.01, 1, 1, 0.99, 0.01, 1, 2, 0.99, 0.01, 1, 0.99, 0.01, 1, 1]

# Command Constants
CMD_RUN = 1
CMD_GET = 2
CMD_STANDBY = 3
CMD_TRACK_1 = 4
CMD_TRACK_2 = 5
CMD_AVOID = 6
CMD_FOLLOW = 7

CMD_Qr_code                = 30
CMD_Barcode                = 31
CMD_Digital_recognition    = 32
CMD_Color_recognition      = 33
CMD_Image_recognition      = 34
CMD_Color_tracking         = 35
CMD_Visual_inspection      = 36
CMD_Traffic_identification = 37
CMD_Machine_learning       = 38
CMD_Face_recognition       = 39

CMD_GRB_RED   = 41
CMD_GRB_GREEN = 42
CMD_GRB_BLUE  = 43

CMD_Take_Stop = 50

tag = "None"

lastTagChangeTime = 0

# Function Mode Constants
FUNCTION_MODES = {
    1: "STANDBY",
    2: "FOLLOW",
    3: "TRACK_1",
    4: "TRACK_2",
    5: "AVOID"
}

ssid = "ESP32-QD003"       # Set WIFI name
password = "12345678"    # Set WIFI password
port = 100               # Setting the server port

dataLen = 0
index_a = 0
buffer = bytearray(52)
prevc = 0
isStart = False
ED_client = True
WA_en = False
sendBuff = ""
val = 0
st = False

function_mode = "STANDBY"
server = None

def readBuffer(index):
    return buffer[index]

def writeBuffer(index, c):
    buffer[index] = c

def setup():
    global server,buzzer_pin,LED1,LED2

    car.move(car.Stop, 0)#car.Stop
    servo_fixed.attach(FIXED_SERVO_PIN)
    servo_fixed.write(90)
    LED1 = Pin(LED_Module1, Pin.OUT)
    LED2 = Pin(LED_Module2, Pin.OUT)
    buzzer_pin = PWM(Pin(buzzer), freq=1000, duty=0) #buzzer init
    wifi = network.WLAN(network.AP_IF)
    wifi.active(True)
    wifi.config(essid=ssid, password=password, max_clients=5,authmode=network.AUTH_WPA2_PSK)
    print("Car Ready! Use 'http://{}' to connect".format(wifi.ifconfig()[0]))
    time.sleep(0.1)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(1)

def RXpack_func():
    global isStart, index_a, dataLen, prevc, st, ED_client, client, server,data,function_mode,previousMillis
    client, _ = server.accept()
    if client:
        WA_en = True
        ED_client = True
        print("[Client connected]")
        previousMillis = time.ticks_ms()
        timeoutDuration = 3000
        while client:
            
            if (time.ticks_ms() - previousMillis) > timeoutDuration and data is None and st==True:
                break
            ready = select.select([client], [], [], 0.01)
            
            if ready[0]:
                try:
                    data = client.recv(1)
                    if data:
                        previousMillis = time.ticks_ms()
                        c = data[0]
                        st = False
                        if c == 200:
                            st = True
                        if c == 0x55 and not isStart:
                            if prevc == 0xff:
                                index_a = 1
                                isStart = True
                        else:
                            prevc = c
                            if isStart:
                                if index_a == 2:
                                    dataLen = c
                                elif index_a > 2:
                                    dataLen -= 1
                                writeBuffer(index_a, c)
                        index_a += 1
                        if index_a > 120:
                            index_a = 0
                            isStart = False
                        if isStart and dataLen == 0 and index_a > 3:
                            isStart = False
                            parseData()
                            index_a = 0
                except OSError as e:
                    client.close()
                    car.move(car.Stop, 0)#car.Stop   
                data = None
            functionMode()
        client.close()
        print("[Client disconnected]")
        car.move(car.Stop, 0)#car.Stop   
    else:
        if ED_client:
          ED_client = False
          

def functionMode():
    global function_mode
    
    if function_mode == "FOLLOW":
        model3_func()
        
    elif function_mode == "TRAFFIC_IDENT":
        Traffic_Task()

    elif function_mode == "TRACK_1":
        model1_func()

    elif function_mode == "TRACK_2":
        model4_func()

    elif function_mode == "AVOID":
        model2_func()

    elif function_mode == "COLOR_TRACKING":
        ColorTracking_Task()

    elif function_mode == "VISUAL_INSPECTION":
        
        cam.servo_write(25)
        VisualInspection_Task()

    

def ColorTracking_Task():
    global lastTagChangeTime
    if cam.color_recognize(readBuffer(12), 200, 200):
        x = cam.getCX
        H = cam.getH

        if (30 <= x <= 240) and (50 <= H <= 70):
            car.move(car.Stop, 0)

        if H > 70:
            car.move(car.Backward, 150)
        elif H < 50:
            car.move(car.Forward, 150)

        if x > 240:
            car.move(car.Clockwise, 150)
        elif x < 30:
            car.move(car.Contrarotate, 150)

        lastTagChangeTime = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), lastTagChangeTime) > 200:
        car.move(car.Stop, 0)

def VisualInspection_Task():
    
    if cam.visual_patrol():
        visualData = cam.Visual_data

        if visualData < -10 and visualData >= -50:
            car.move(car.Stop, 0)
            time.sleep_ms(30)
            car.move(car.Clockwise, 90)

        elif visualData <= 15 and visualData >= -10:
            car.move(car.Forward, 110)

        elif visualData <= 52 and visualData > 15:
            car.move(car.Stop, 0)
            time.sleep_ms(30)
            car.move(car.Contrarotate, 90)

        else:
            car.move(car.Clockwise, 100)
            time.sleep_ms(10)

def Traffic_Task():
    global tag, lastTagChangeTime, function_mode
    
    if cam.Traffic_recognize(1):
        tag = cam.getTag
        lastTagChangeTime = time.ticks_ms()
    
    if tag != "None" and time.ticks_diff(time.ticks_ms(), lastTagChangeTime) > 500:

        if tag == "Go_Straight":
            car.move(car.Forward, 180)
            time.sleep_ms(500)

        elif tag == "Turn_Right":
            car.move(car.Clockwise, 180)
            time.sleep_ms(500)

        elif tag == "Turn_Left":
            car.move(car.Contrarotate, 180)
            time.sleep_ms(500)

        elif tag == "Turn_Around":
            car.move(car.Forward, 180)
            time.sleep_ms(1450)
            car.move(car.Clockwise, 180)
            time.sleep_ms(1600)
            car.move(car.Forward, 180)
            time.sleep_ms(1300)

        elif tag == "Throughout":
            car.move(car.Stop, 180)
            time.sleep_ms(500)

        tag = "None"
        
        car.move(car.Stop,0)


def parseData():
    global function_mode,r,g,b
    action = readBuffer(9)
    device = readBuffer(10)
    
    if action == CMD_RUN:
        function_mode = "STANDBY"
        runModule(device)
    elif action == CMD_STANDBY:
        function_mode = "STANDBY"
        car.move(car.Stop, 255)#st
    elif action == CMD_TRACK_1:
        function_mode = "TRACK_1"
    elif action == CMD_TRACK_2:
        function_mode = "TRACK_2"
    elif action == CMD_AVOID:
        function_mode = "AVOID"
    elif action == CMD_FOLLOW:
        function_mode = "FOLLOW"
    # ---------- AI CAMERA FUNCTIONS ----------
    if device == CMD_Qr_code:
        cam.qrcode_recognize()
        car.move(car.Stop,0)
        
    elif device == CMD_Barcode:
        cam.barcode_recognize()
        car.move(car.Stop,0)

    elif device == CMD_Digital_recognition:
        cam.number_recognize()
        car.move(car.Stop,0)

    elif device == CMD_Color_recognition:
        cam.color_recognize(3, 200, 200)
        car.move(car.Stop,0)

    elif device == CMD_Image_recognition:
        cam.image_recognize()
        car.move(car.Stop,0)
        
    elif device == CMD_Color_tracking:
        function_mode = "COLOR_TRACKING"

    elif device == CMD_Visual_inspection:
        function_mode = "VISUAL_INSPECTION"

    elif device == CMD_Traffic_identification:
        function_mode = "TRAFFIC_IDENT"

    elif device == CMD_Machine_learning:
        cam.machine_learning()
        car.move(car.Stop,0)

    elif device == CMD_Face_recognition:
        cam.face_recognize()
        car.move(car.Stop,0)

    elif device == CMD_GRB_RED:
        r = readBuffer(12)
        cam.RGB_set(r, g, b)

    elif device == CMD_GRB_GREEN:
        g = readBuffer(12)
        cam.RGB_set(r, g, b)
        
    elif device == CMD_GRB_BLUE:
        b = readBuffer(12)
        cam.RGB_set(r, g, b)
        
    elif device == CMD_Take_Stop:
        cam.Default_menu()
        cam.servo_write(90)
        car.move(car.Stop,0)
    else:
        pass
    
def Buzzer_run(M):
    if M == 0x01:
        play_music(tune0, durt0, 0.5)
    elif M == 0x02:
        play_music(tune1, durt1, 0.5)
    elif M == 0x03:
        play_music(tune2, durt2, 0.5)
    elif M == 0x04:
        play_music(tune3, durt3, 0.3)

# Define the function to play the music
def play_music(tune, durt, delay_time):
    while True:
        for i in range(len(tune)):
            if tune[i] is not None:
                freq = int(tune[i])
                if freq < 1:
                    freq = 1
                elif freq > 40000000:
                    freq = 40000000
                buzzer_pin.freq(freq)
                buzzer_pin.duty_u16(32767)  # 50% duty cycle
            time.sleep(delay_time * durt[i])
            buzzer_pin.duty_u16(0)  # Turn off the buzzer
            time.sleep(delay_time * durt[i] * 0.1)  # Add a small delay between notes
        break


#track mode1
def model1_func():
    Left_Tra_Value = adc1.read() #Read the value of left tracking sensor
    Right_Tra_Value = adc2.read()
    time.sleep(0.0005)
#         print(Left_Tra_Value)
    if Left_Tra_Value < Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 150)
    elif Left_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Contrarotate, 150)
    elif Left_Tra_Value < Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Clockwise, 150)
    elif Left_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Stop, 0)
        

def model4_func():
    Left_Tra_Value = adc1.read() 
    Right_Tra_Value = adc2.read()
    Middle_Tra_Value = adc3.read()
    time.sleep(0.0005)

    if Left_Tra_Value < Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 130)
        
    if Left_Tra_Value < Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Forward, 130)
    
    if Left_Tra_Value >= Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 130)
        
    elif Left_Tra_Value >= Black_Line and Middle_Tra_Value < Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Contrarotate, 180)
    
    elif Left_Tra_Value < Black_Line and Middle_Tra_Value < Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Clockwise, 180)
        
    elif Left_Tra_Value >= Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Forward, 130)
    

# follow
def model3_func():
    servo_fixed.write(90)
    
    UT_distance = Ultrasonic.get_distance()
    
    if UT_distance < 15:
        car.move(car.Backward, 200)
    elif 15 <= UT_distance and UT_distance <= 20:
        car.move(car.Stop, 0)
    elif 20 <= UT_distance and UT_distance <= 25:
        car.move(car.Forward, speeds-70)
    elif 25 <= UT_distance and UT_distance <= 50:
        car.move(car.Forward, 220)
    else:
        car.move(car.Stop, 0)
        
def model2_func():
    servo_fixed.write(90)
    UT_distance = Ultrasonic.get_distance()
    middleDistance = UT_distance
    
    if middleDistance <= 25:
        car.move(car.Stop, 0)
        time.sleep(0.5)
        servo_fixed.write(45)
        time.sleep(0.3)
        rightDistance = Ultrasonic.get_distance()
        servo_fixed.write(135)
        time.sleep(0.3)
        leftDistance = Ultrasonic.get_distance()
        servo_fixed.write(90)
        if rightDistance < 10 and leftDistance < 10:
            car.move(car.Backward, 180)
            time.sleep(1)
            car.move(car.Contrarotate, 180)
            time.sleep(0.5)
        elif rightDistance < leftDistance:
            car.move(car.Backward, 180)
            time.sleep(0.5)
            car.move(car.Contrarotate, 180)
            time.sleep(0.5)
        elif rightDistance > leftDistance:
            car.move(car.Backward, 180)
            time.sleep(0.5)
            car.move(car.Clockwise, 180)
            time.sleep(0.5)
        else:
            car.move(car.Backward, 180)
            time.sleep(0.5)
            car.move(car.Clockwise, 180)
            time.sleep(0.5)
    else:
        car.move(car.Forward, 150)
        
    
def runModule(device):
    global speeds
    val = readBuffer(12)
    if device == 0x0C:
        if val == 0x01:
            car.move(car.Forward, speeds)#car.Forward
        elif val == 0x02:
            car.move(car.Backward, speeds)#car.Backward
        elif val == 0x03:
            car.move(car.move_Left, speeds)#car.move_Left
        elif val == 0x04:
            car.move(car.move_Right, speeds)#car.move_Right
        elif val == 0x05:
            car.move(car.Top_Left, speeds)#car.Top_Left
        elif val == 0x06:
            car.move(car.Bottom_Left, speeds)#car.Bottom_Left
        elif val == 0x07:
            car.move(car.Top_Right, speeds)#car.Top_Right
        elif val == 0x08:
            car.move(car.Bottom_Right, speeds)#car.Bottom_Right
        elif val == 0x0A:
            car.move(car.Clockwise, speeds)#car.Clockwise
        elif val == 0x09:
            car.move(car.Contrarotate, speeds)#car.Contrarotate
        elif val == 0x00:
            car.move(car.Stop, 0)#car.Stop
    elif device == 0x03:
        Buzzer_run(val)  #buzzer
    elif device == 0x05:
        LED1.value(val)
        LED2.value(val)
    elif device == 0x08:
        shoot_pin = Pin(Shoot_PIN, Pin.OUT)  #shoot
        shoot_pin.value(1)  # high
        time.sleep_ms(150) 
        shoot_pin.value(0)  # low
    elif device == 0x0D:
        speeds = val

setup()

while True:
    RXpack_func()

