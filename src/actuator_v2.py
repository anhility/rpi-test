# USE ON RASPBERRY PI

import socket
import RPi.GPIO as GPIO
import threading
import time

# Pin voltage
HIGH = GPIO.HIGH
LOW = GPIO.LOW

# Networking
SRC_IP = '10.35.0.1'
DST_IP = '10.34.0.1'
PORT = 5005

# Message
SNT_MSG = 'hello' # The hello message
MSG_ENC = 'UTF-8' # Message encoding.

# Check socket
# If new data exists, reset dead timer.
# # Check what kind of data
# # Requires a flag to check if there's new data.
# #

# Listens on UDP packets and returns the decoded data, as long as it's from the right IP and port.
def listenonUDP(clientsocket):
    try:
        data, (address, port) = clientsocket.recvfrom(1024)
        if str(address) == DST_IP and int(port) == PORT:
            return data.decode(MSG_ENC)
        else:
            return 255
    except KeyboardInterrupt:
        clientsocket.clean()
        GPIO.cleanup()
        sys.exit()
    except:
        return 255
# Thread1, lights LEDs.
def lightState(clientsocket):
    lock = threading.Lock()
    flag = 0        # Used for if statements, so they don't mess up the timers. 1 means a 1 has already been received.
    deadtimer = time.time()   # Used for printing messages on screen if timer gets too great.
    lighttimer = 0.0
    while True:
        data = listenonUDP(clientsocket)
        if data != 255:
            deadtimer = time.time()
        if data == '1' and flag == 0:
            flag = 1
            lighttimer = time.time()
            GPIO.output(7, HIGH)
        elif data == '0' and flag == 1:
            flag = 0
            lighttimer = time.time()
            GPIO.output(7, LOW)
            GPIO.output(11, LOW)
        elif time.time() - lighttimer > 5 and flag == 1:
            GPIO.output(11, HIGH)
        # Light on pin 11, still left to fix.
        if time.time() - deadtimer >= 4.0:
            print('No connection to the other pi')
            deadtimer = time.time()

# Thread2, sends hello packets.
def sendUDP(clientsocket):
    lock = threading.Lock()
    timer = time.time()
    while True:
        if time.time() - timer >= 0.5:
            lock.acquire()
            clientsocket.sendto(bytes(SNT_MSG, MSG_ENC), (DST_IP, PORT))
            lock.release()
            timer = time.time()

def main():
    print('Running program')
    GPIO.setmode(GPIO.BOARD)        # Sets pin mode to BOARD (Pin numbers)
    GPIO.setwarnings(False)         # Suppresses startup warnings.
    GPIO.setup(7, GPIO.OUT)         # Sets pins as output.
    GPIO.setup(11, GPIO.OUT)
    GPIO.output(7, LOW)             # Turns off lights at startup
    GPIO.output(11, LOW)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsocket.bind((SRC_IP, PORT)) # Binds the IP and port to the pi. Prevents the socket from closing.
    clientsocket.setblocking(False)
    # Makes the functions lightState and sendUDP into threads and sends clientsocket as argument.
    t1 = threading.Thread(target = lightState, args = (clientsocket,))
    t2 = threading.Thread(target = sendUDP, args = (clientsocket,))

    # Starts the threads.
    t1.start()
    t2.start()

main()
