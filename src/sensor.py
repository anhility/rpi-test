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
MSG_UDP     = None              # Message variable
ENC_TYPE    = 'UTF-8'           # Message encoding
PKT_COPY    = 3                 # Amount of copies to send
SKT_TIMEOUT = 0.1               # Timeout for socket listening

## Timers ##
TIMER_HELLO     = None          # Timer for sending hello
T_HELLO_UPDATE  = 0.5           # Update frequency

TIMER_STATE     = None          # Timer for state check from thermometer
T_STATE_UPDATE  = 0.1           # Update frequency

TIMER_DEAD      = None          # Timer for dead check of actuator
T_DEAD_MAX      = 4             # Max time before assumed dead

## Variables ##
STATE           = False         # Default state
MSG_HELLO       = "hello"       # Hello message
MSG_GET_STATE   = "getState"    # GetState message
POLL_TIME       = 10            # ms to wait between each loop cycle
MAX_TEMP        = 26            # Max temperature before changing state to True
PIN_LED         = 17            # BCM pin number for LED
RAND_TYPE       = True          # True: drop 1 of n packets.
                                # False: Send 1 of n packets.
RAND_MOD        = 1             # Modulo for randrange where n >= 1.
                                # Set to 1 to always send packet.

### Error Flags ###
ERR_A_DEAD      = False         # True if Actuator is dead

### Temperature file manipulation ###
# Loading drivers for check of temperature file
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
# Location of temperature file
temp_sensor = '/sys/bus/w1/devices/28-000009367a30/w1_slave'

### Functions ###

def sendUDP(data):
    lock = threading.Lock()
    lock.acquire()
    # Simple transmission with encoding to target ip/port
    SKT.sendto(bytes(data, ENC_TYPE), (IP_TRG, UDP_PORT))
    lock.release()
    return

def listenUDP():
    global MSG_UDP, TIMER_DEAD, ERR_A_DEAD
    
    # Ugly try-except test to let the socket time-out
    # without stopping the script
    try:
        lock = threading.RLock()
        lock.acquire()
        data, conn_address = SKT.recvfrom(1024)
        lock.release()
        if str(conn_address[0]) == IP_TRG and int(conn_address[1]) == UDP_PORT:
            global MSG_UDP
            MSG_UDP = data.decode(ENC_TYPE)
    except:
        pass
    
    if MSG_UDP == MSG_HELLO:
        # If hello, reset timer and error
        TIMER_DEAD = time.time()
        if ERR_A_DEAD == True:
            ERR_A_DEAD = False
    elif MSG_UDP == MSG_GET_STATE:
        # If getState, send state
        sendState(PKT_COPY)
        ERR_A_DEAD = False
    elif time.time() - TIMER_DEAD > T_DEAD_MAX:
        # If no hello and timer maxed out, set error
        ERR_A_DEAD = True
    
    MSG_UDP = None
    return

def readTemp():
    global STATE
    
    f = open(temp_sensor, 'r')
    # Extraction of temperature data from file
    temp_c = float(((f.readlines())[1])[-6:]) / 1000.0
    f.close()

    print(temp_c)

    if temp_c > MAX_TEMP and STATE == False:
        STATE = True
    elif temp_c <= MAX_TEMP and STATE == True:
        STATE = False
    return

def updateLamp(state):
    GPIO.output(PIN_LED, state)
    return

def sendState(num = 1):
    # Default number of copies to send is 1 
    for i in range(num):
        # If RAND_MOD == 1, always send
        if RAND_MOD == 1:
            sendUDP(str(STATE))
        elif RAND_TYPE == True:
            # Drop 1 of n packets
            if random.randrange(RAND_MOD) != 0:
                sendUDP(str(STATE))
        else:
            # Send 1 of n packets
            if random.randomrange(RAND_MOD) == 0:
                sendUDP(str(STATE))
    return

def threadCheckState():
    # Checking the state
    while True:
        # Copy of state to compare against
        compareState = STATE
        # Sleep to let threadReadTemp() update the state
        time.sleep(POLL_TIME / 1000.0)

        # If STATE have changed, send update
        if compareState != STATE:
            sendState(PKT_COPY)

def threadReadTemp():
    # Temperature polling
    while True:
        if time.time() - TIMER_STATE > T_STATE_UPDATE:
            readTemp()

def threadListenUDP():
    # Listen for UDP packets
    while True:
        listenUDP()

def threadSendHello():
    # Sends hello packets on a timer
    while True:
        global TIMER_HELLO
        if time.time() - TIMER_HELLO > T_HELLO_UPDATE:
                sendUDP(MSG_HELLO)
                TIMER_HELLO = time.time()

def threadLampUpdate():
    # update lamp
    while True:
        # Copy of state to compare against
        compareState = STATE
        # Sleep to let threadReadTemp() update the state
        time.sleep(POLL_TIME / 1000.0)
        
        if compareState != STATE and ERR_A_DEAD == False:
            # If state changed and actuator is alive, change led state
            updateLamp(STATE)
        elif ERR_A_DEAD == True:
            # If actuator is dead, blink led
            if (time.time() - TIMER_DEAD)%1 > 0.5:
                updateLamp(True)
            else:
                updateLamp(False)
        elif ERR_A_DEAD == False:
            # If state is same and actuator is alive again, turn of led
            updateLamp(STATE)

### Main Function ###
def main():
    
    ### Initialization ###
    ## Calling Globals ##
    global SKT, TIMER_HELLO, TIMER_STATE, TIMER_DEAD

    ## Timer Setup ##
    initTime    = time.time()
    TIMER_HELLO = initTime
    TIMER_STATE = initTime
    TIMER_DEAD  = initTime

    ## Socket Setup ##
    SKT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SKT.bind((IP_SRC, UDP_PORT))
    SKT.settimeout(SKT_TIMEOUT)
    
    ## GPIO Setup ##
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_LED, GPIO.OUT)
    GPIO.output(PIN_LED, False)
    
    ### Initialization Complete ###
    
    ### Creation and start of threads ###
    # Thread to check if state has been changed
    t1 = threading.Thread(target=threadCheckState, name="CheckState", daemon=True)

    # Thread to send hello messages to actuator
    t2 = threading.Thread(target=threadSendHello, name="SendHello", daemon=True)

    # Thread for lamp control
    t3 = threading.Thread(target=threadLampUpdate, name="LampUpdate", daemon=True)

    # Thread to listen for UDPs
    t4 = threading.Thread(target=threadListenUDP, name="ListenUDP", daemon=True)

    # Thread to read temperature
    t5 = threading.Thread(target=threadReadTemp, name="ReadTemp", daemon=True)
    
    # Start of threads
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()

    ## Exit gracefully with ^C or ^D ##
    while True:
        try:
            _ = input()
        except (KeyboardInterrupt, EOFError) as err:
            SKT.close()
            GPIO.cleanup()
            print("Script terminated.")
            sys.exit()


print("Sensor activated")
main()
