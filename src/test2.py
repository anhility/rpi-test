# USE ON RASPBERRY PI

import socket
import RPi.GPIO as GPIO
import threading
import time

# Pin voltage
HIGH = GPIO.HIGH
LOW = GPIO.HIGH

# Networking
SRC_IP = '10.35.0.1'
DST_IP = '10.0.0.2'
PORT = 5005

# Message
SNT_MSG = 'hello'
MSG_ENC = 'UTF-8'

# Sets the state of the light.
def lightState(light, data)
    if data == 1:
        GPIO.output(pin, HIGH
    elif state == 0:
        GPIO.output(pin, LOW)

# Threaded, listens on UDP data.
def listenonUDP(clientsocket):
    lock = threading.Lock()
    while True:
        lock.acquire()
        data = clientsocket.recv(1024)
        print(data.decode(MSG_ENC))
        lock.release()
        if data.decode != 'hello':
            timer = time.time()
            lightState(7, data)

# Threaded, sends hello packets.
def sendUDP(clientsocket):
    lock = threading.Lock()
    while True:
        lock.acquire()
        clientsocket.sendto(bytes(SNT_MSG, MSG_ENC), (DST_IP, PORT))
        lock.release()

def main():
    print('Running program')
    GPIO.setmode(GPIO.BOARD)        # Sets pin mode to BOARD (Pin numbers)
    GPIO.setwarnings(False)         # Suppresses startup warnings.
    GPIO.setup(7, GPIO.OUT)         # Sets pins as output.
    GPIO.setup(11, GPIO.OUT)
    GPIO.output(7, LOW)             # Turns off lights at startup
    GPIO.output(11, LOW)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsocket.bind((SRC_IP, PORT))

    # Makes the functions ListenonUDP and sendUDP into threads and sends clientsocket as argument.
    t1 = threading.Thread(target = listenonUDP, args = (clientsocket,))
    t2 = threading.Thread(target = sendUDP, args = (clientsocket,))

    # Starts the threads.
    t1.start()
    t2.start()


main()
