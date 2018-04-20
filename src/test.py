# USE ON LAPTOP FOR TESTING

import threading
import time
import socket

# Network
SRC_IP = '10.0.0.2'
DST_IP = '10.35.0.1'
PORT = 5005

# Message
SNT_MSG = 'hello'
MSG_ENC = 'UTF-8'

def main():
    print('Running program')
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsocket.bind((SRC_IP, PORT))
    while True:
        message = input()
        clientsocket.sendto(bytes(message, MSG_ENC), (DST_IP, PORT))
    clientsocket.close()
    print('Exiting program')

main()
