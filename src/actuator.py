import RPi.GPIO as GPIO
import threading
import time
import socket

### Global Variables ###
## Connectivity ##
UDP = None                  # UDP anchor
TARGET_IP = "10.34.0.1"      # IP to actuator
UDP_PORT = 5005             # Port to listen/send on
UDP_MSG = None              # Received message

## Timers ##
TIMER_HELLO = None          # Timer for sending hello
T_HELLO_UPDATE = 0.1        # Update frequency

TIMER_DEAD = None           # Timer for dead check of sensor
T_DEAD_UPDATE = 0.1         # Update frequency
T_DEAD_MAX = 4              # Max time before assumed dead

## Variables ##
STATE = False               # Default state
HELLO = "hello"             # Hello message
GET_STATE = "getState"      # GetState message
POLL_TIME = 10              # ms to wait between each loop cycle
HIGH = GPIO.HIGH
LOW = GPIO.LOW

DEBUG = True                # Set to true for debug info

### Errors ###
ERR_S_DEAD = False          # Sensor is dead

### Functions ###
def init():
    GPIO.setmode(GPIO.BOARD)        # Sets pin mode to BOARD (Pin numbers)
    GPIO.setwarnings(False)         # Suppresses startup warnings.
    GPIO.setup(7, GPIO.OUT)         # Sets pins as output.
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(13, GPIO.OUT)
    GPIO.output(7, LOW)             # Turns off lights at startup.
    GPIO.output(11, LOW)
    GPIO.output(13, LOW)

    global UDP, TIMER_HELLO, TIMER_DEAD
    initTime    = time()
    TIMER_HELLO = initTime
    TIMER_DEAD  = initTime

    ## UDP Setup ##
    
    #UDP = UDPSocket()
    #UDP.begin(UDP_PORT)

    ## Zeroize output ##
    #updateFan(False)

    ## Send hello ##
    #sendUDP(HELLO)

    ## Request state ##
    #sendUDP(GET_STATE)
    
    return


#def error(num):
#    return

def sendUDP(data):
    UDP.send(TARGET_IP, UDP_PORT, data)
    return

def onUDPReceive(_, _, data):
    global UDP_MSG
    UDP_MSG = data
    return

def listenUDP():
    global UDP_MSG, STATE, TIMER_DEAD, ERR_S_DEAD
    
    #UDP.onReceive(onUDPReceive)
    
    if UDP_MSG == HELLO:
        TIMER_DEAD = time()
        ERR_S_DEAD = False
    elif UDP_MSG == "true":
        STATE = True
        TIMER_DEAD = time()
        ERR_S_DEAD = False
    elif UDP_MSG == "false":
        STATE = False
        TIMER_DEAD = time()
        ERR_S_DEAD = False
    elif time() - TIMER_DEAD > T_DEAD_MAX:
        ERR_S_DEAD = True
    
    #print UDP_MSG
    UDP_MSG = None
    return

def updateFan(state):
    if state == False:
        
        customWrite(0, 0)
    else:
        
        customWrite(0, 2)
    return

def customtimer(state)
    if state == 1:
    time 

### Main Function ###
def main():
    
    pinMode(0, OUT)            # Signal to light
    
    ## Initialization ##
    init()
    
    ## Main loop ##
    while True:
        
        compareState = STATE
        time.sleep(POLL_TIME / 1000.0)
        
        # Send hello
        if time() - TIMER_HELLO > T_HELLO_UPDATE:
            sendUDP("hello")
        
        # listen
        listenUDP()
        
        # update fan
        #print "Uptime: %s, State: %s, Sensor: %s" % (uptime(), STATE, ERR_S_DEAD)
        
        if compareState != STATE and ERR_S_DEAD == False:
            updateFan(STATE)
        elif ERR_S_DEAD == True:
            if (time() - TIMER_DEAD)%1 > 0.5:
                updateFan(True)
            else:
                updateFan(False)
        elif ERR_S_DEAD == False:
            updateFan(STATE)
    

main()
