import time, math
#TODO: Import & implement SOCKET/UDP
from udp import *
#TODO: Import & implement rpi.gpio
from gpio import *

### Global Variables ###
## Connectivity ##
UDP         = None              # UDP anchor
TARGET_IP   = "10.0.0.2"        # IP to actuator
UDP_PORT    = 5005              # Port to listen/send on
UDP_MSG     = None              # Received message

## Timers ##
TIMER_HELLO     = None          # Timer for sending hello
T_HELLO_UPDATE  = 0.1           # Update frequency

TIMER_STATE     = None          # Timer for state check from thermometer
T_STATE_UPDATE  = 0.5           # Update frequency

TIMER_DEAD      = None          # Timer for dead check of actuator
T_DEAD_UPDATE   = 0.1           # Update frequency
T_DEAD_MAX      = 4             # Max time before assumed dead

## Variables ##
STATE           = False         # Default state
HELLO           = "hello"       # Hello message
GET_STATE       = "getState"    # GetState message
POLL_TIME       = 10            # ms to wait between each loop cycle
MAX_TEMP        = 26            # Max temperature before changing state to True
DEBUG           = True          # Set to true for debug info

### Errors ###
ERR_A_DEAD      = False         # Actuator is dead

### Functions ###
def init():
    
    global UDP, TIMER_HELLO, TIMER_STATE, TIMER_DEAD
    initTime    = time()
    TIMER_HELLO = initTime
    TIMER_STATE = initTime
    TIMER_DEAD  = initTime

    ## UDP Setup ##
    #TODO: Changet to SOCKET
    UDP = UDPSocket()
    UDP.begin(UDP_PORT)
    
    ## Zeroize output ##
    updateLamp(False)
    sendState(False, 3)
    
    ## Send hello ##
    sendUDP(HELLO)
    
    ## Read temperature ##
    readTemp()
    
    ## Update Lamp ##
    updateLamp(STATE)
    
    ## Send State ##
    sendState(STATE, 3)
    
    return

#TODO: Add error output
#def error(num):
#    return

def sendUDP(data):
    UDP.send(TARGET_IP, UDP_PORT, data)
    return

def onUDPReceive(ip, port, data):
    global UDP_MSG
    UDP_MSG = data
    return

def listenUDP():
    global UDP_MSG, TIMER_DEAD, ERR_A_DEAD
    
    UDP.onReceive(onUDPReceive)
    
    if UDP_MSG == HELLO:
        TIMER_DEAD = time()
        ERR_A_DEAD = False
    elif UDP_MSG == GET_STATE:
        sendState(STATE, 3)
        ERR_A_DEAD = False
    elif time() - TIMER_DEAD > T_DEAD_MAX:
        ERR_A_DEAD = True
    
    #print UDP_MSG
    UDP_MSG = None
    return

def readTemp():
    global STATE
    #TODO: Change to valid gpio
    if float(customRead(0)) > MAX_TEMP and STATE == False:
        STATE = True
    elif float(customRead(0)) <= MAX_TEMP and STATE == True:
        STATE = False
    return

def updateLamp(state):
    #TODO: Change to valid gpio
    if state == False:
        digitalWrite(1, LOW)
    else:
        digitalWrite(1, HIGH)
    return

def sendState(state, num):
    for i in range(num - 1):
        if state == False:
            sendUDP("false")
        else:
            sendUDP("true")
    return

### Main Function ###
def main():
    #TODO: Change to valid gpio
    pinMode(0,IN)    # Read temperature
    pinMode(1, OUT) # Signal to lamp
    
    ## Initialization ##
    init()
    
    ## Main loop ##
    while True:
        
        compareState = STATE
        time.sleep(POLL_TIME / 1000.0)
    
        # Send hello
        if time() - TIMER_HELLO > T_HELLO_UPDATE:
            sendUDP(HELLO)
        # listen
        listenUDP()
        
        # read temp
        if time() - TIMER_STATE > T_STATE_UPDATE:
            readTemp()
            
        # update lamp
        #print "Uptime: %s, State: %s, Actuator: %s" % (uptime(), STATE, ERR_A_DEAD)
        
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
            sendState(STATE, 3)
        

if __name__ == "__main__":
    print("Sensor activated")
    main()