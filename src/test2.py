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

def listenonUDP(clientsocket):
    #lock = threading.Lock()
    print('Starting listenonUDP')
    while True:
        #lock.acquire()
        message = clientsocket.recv(1024)
        print(message.decode(MSG_ENC))
        #lock.release()

def sendUDP(clientsocket):
    lock = threading.Lock()
    print('Starting sendUDP')
    #timer = time.time()
        #if timer < time.time()/2:
        #lock.acquire()
    while True:
        lock.acquire()
        clientsocket.sendto(bytes(SNT_MSG, MSG_ENC), (DST_IP, PORT))
        lock.release()
        #timer = time.time()

def main():
    print('Running program')
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsocket.bind((SRC_IP, PORT))

    t1 = threading.Thread(target = listenonUDP, args = (clientsocket,))
    t2 = threading.Thread(target = sendUDP, args = (clientsocket,))
    t1.start()
    t2.start()

main()


