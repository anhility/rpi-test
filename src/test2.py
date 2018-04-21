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
DST_IP = '10.0.0.2'
PORT = 5005

# Message
SNT_MSG = 'hello' # The hello message
MSG_ENC = 'UTF-8' # Message encoding.

# Sets the state of the light. 1 for on, 0 for off. Uses the received data.
def lightState(pin, data):
    if data == '1':
        GPIO.output(pin, HIGH)
    elif data == '0':
        GPIO.output(pin, LOW)

# Thread1, listens on UDP data.
def listenonUDP(clientsocket):
    lock = threading.Lock()
    while True:
        lock.acquire()
        data = clientsocket.recv(1024)
        #print(data.decode(MSG_ENC))
        lock.release()
        if data.decode != '1':
            timer = time.time() # Starts a timer. Used for determining when to light the second light.
            while data.decode != '0':
                lock.acquire()
                data = clientsocket.recv(1024)
                lock.release()
                lightState(7, data.decode(MSG_ENC))
                if timer - time.time() > 5:
                    lightState(11, data.decode(MSG_ENC))
            # Turns off lights only after receiving a 0.
            lightState(7, data.decode(MSG_ENC))
            lightState(11, data.decode(MSG_ENC))

# Thread2, sends hello packets.
def sendUDP(clientsocket):
    lock = threading.Lock()
    while True:
        timer = time.time() # Timer used for setting the frequency of keep-alives.
        if time.time() - timer > 0.5:
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

    # Makes the functions ListenonUDP and sendUDP into threads and sends clientsocket as argument.
    t1 = threading.Thread(target = listenonUDP, args = (clientsocket,))
    t2 = threading.Thread(target = sendUDP, args = (clientsocket,))

    # Starts the threads.
    t1.start()
    t2.start()

main()
