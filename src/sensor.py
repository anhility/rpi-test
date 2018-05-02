'''
Created on 14 apr. 2018

@author: Mike
'''

import os, time, socket, threading, random, sys
import RPi.GPIO as GPIO

### Global Variables ###
## Connectivity ##
SKT         = None              # Socket anchor
IP_SRC      = "10.34.0.1"       # Local IP
IP_TRG      = "10.35.0.1"       # IP to actuator
UDP_PORT    = 5005              # Port to listen/send on
UDP_MSG     = None              # Message varaible
MSG_ENC     = 'UTF-8'           # Message encoding
PKT_COPY    = 3                 # Amount of copies to send for state update

## Timers ##
TIMER_HELLO     = None          # Timer for sending hello
T_HELLO_UPDATE  = 0.5           # Update frequency

TIMER_STATE     = None          # Timer for state check from thermometer
T_STATE_UPDATE  = 0.1           # Update frequency

TIMER_DEAD      = None          # Timer for dead check of actuator
T_DEAD_UPDATE   = 0.1           # Update frequency
T_DEAD_MAX      = 4             # Max time before assumed dead

## Variables ##
STATE           = False         # Default state
HELLO           = "hello"       # Hello message
GET_STATE       = "getState"    # GetState message
POLL_TIME       = 10            # ms to wait between each loop cycle
MAX_TEMP        = 26            # Max temperature before changing state to True
PIN_LED         = 17            # BCM pin number for LED
RAND_MOD        = 1             # Modulo for randrange where n >= 1.

### Error Flags ###
ERR_A_DEAD      = False         # If Actuator is dead

### Temperature file manipulation ###
# Loading drivers for check of temperature file
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
# Location of temperature file
temp_sensor = '/sys/bus/w1/devices/28-000009367a30/w1_slave'

### Functions ###

def sendUDP(data):
    SKT.sendto(bytes(data, MSG_ENC), (IP_TRG, UDP_PORT))
    return

def onUDPReceive():
    try:
        data, (recvIP, recvPort) = SKT.recvfrom(1024)
        if str(recvIP) == IP_TRG and int(recvPort) == UDP_PORT:
            global UDP_MSG
            UDP_MSG = data.decode(MSG_ENC)
        else:
            return
    except KeyboardInterrupt:
        SKT.clean()
        GPIO.cleanup()
        print("Script terminated.")
        sys.exit()

def listenUDP():
    global UDP_MSG, TIMER_DEAD, ERR_A_DEAD
    
    onUDPReceive()
    
    if UDP_MSG == HELLO:
        TIMER_DEAD = time.time()
        ERR_A_DEAD = False
    elif UDP_MSG == GET_STATE:
        sendState(STATE, PKT_COPY)
        ERR_A_DEAD = False
    elif time() - TIMER_DEAD > T_DEAD_MAX:
        ERR_A_DEAD = True
    
    UDP_MSG = None
    return

def readTemp():
    global STATE
    
    f = open(temp_sensor, 'r')
    temp_c = float((f.readlines())[1].lstrip(-5)) / 1000.0
    f.close()
    
    if temp_c > MAX_TEMP and STATE == False:
        STATE = True
    elif temp_c <= MAX_TEMP and STATE == True:
        STATE = False
    return

def updateLamp(state):
    GPIO.output(PIN_LED, state)
    return

def sendState(state, num = None):
    if num == None:
        num = 1
    for i in range(num):
        if random.randrange(RAND_MOD) == 0:
            sendUDP(state)
    return

def loopMain():
    # Main loop
    lock = threading.Lock()
    while True:
        
        compareState = STATE
        time.sleep(POLL_TIME / 1000.0)
        
        # listen
        lock.aquire()
        listenUDP()
        lock.release()
        
        # read temp
        if time() - TIMER_STATE > T_STATE_UPDATE:
            readTemp()
            
        # update lamp
        if compareState != STATE and ERR_A_DEAD == False:
            updateLamp(STATE)
        elif ERR_A_DEAD == True:
            if (time() - TIMER_DEAD)%1 > 0.5:
                updateLamp(True)
            else:
                updateLamp(False)
        elif ERR_A_DEAD == False:
            updateLamp(STATE)

        # send state
        if compareState != STATE:
            lock.aquire()
            sendState(STATE, 3)
            lock.release()


def loopSendHello():
    # Sends hello packets on a timer
    global TIMER_HELLO
    lock = threading.Lock()
    if time() - TIMER_HELLO > T_HELLO_UPDATE:
            lock.acquire()
            sendUDP(HELLO)
            lock.release()
            TIMER_HELLO = time.time()

### Main Function ###
def main():
    
    ### Initialization ###
    
    global SKT, TIMER_HELLO, TIMER_STATE, TIMER_DEAD
    initTime    = time.time()
    TIMER_HELLO = initTime
    TIMER_STATE = initTime
    TIMER_DEAD  = initTime

    ## Socket Setup ##
    SKT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SKT.bind((IP_SRC, UDP_PORT))
    SKT.setblocking(False)
    
    ## GPIO init ##
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_LED, GPIO.OUT)
    GPIO.output(PIN_LED, False)
    
    ## Zeroize output ##
    GPIO.output(PIN_LED, False)
    sendState(False, PKT_COPY)
    
    ## Send hello ##
    sendUDP(HELLO)
    
    ## Read temperature ##
    readTemp()
    
    ## Update Lamp ##
    updateLamp(STATE)
    
    ## Send State ##
    sendState(STATE, PKT_COPY)
    ### Initialization Complete ###
    
    ## Creation and start of threads ##
    # Separate thread to send hello message uninterrupted
    t1 = threading.Thread(target=loopSendHello)
    # Main loop thread
    t2 = threading.Thread(target=loopMain)
    # Start of threads
    t1.start()
    t2.start()


print("Sensor activated")
main()
