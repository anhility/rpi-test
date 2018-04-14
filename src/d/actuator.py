from gpio import *
from time import *
from udp import *

def init():
    return

def sendUDP(data):
    return

def helloSend():
    return
	
def helloListen():
    return
	
def requestState():
    return
	
def listenState():
    return
	
def updateFan(state):
    return
	
def error(num):
    return

def onUDPReceive(ip, port, data):
    print(data)
    if int(data) == 1:
        customWrite(0, 2)
    else:
        customWrite(0, 0)

def main():
    pinMode(0, OUT)
    udp = UDPSocket()
    udp.begin(2000)
    print("Running program")
    while True:
        udp.onReceive(onUDPReceive)
        delay(500)
main()
