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

D_TIME = 4 # Maximum dead time in seconds.

# Flashes lights. Used in conjunction with dead timer.
# If the timer exceeds threshold, flash lights.
def lightFlash():
    GPIO.output(11, HIGH)
    time.sleep(0.2)
    GPIO.output(11, LOW)
    time.sleep(0.2)

# Listens on UDP packets and returns the decoded data, as long as it's from the right IP and port.
def listenonUDP(clientsocket):
    lock = threading.Lock()
    try:
        lock.acquire()
        data, (address, port) = clientsocket.recvfrom(1024)
        lock.release()
        if str(address) == DST_IP and int(port) == PORT:
            return data.decode(MSG_ENC) # return decoded data for use in the function lightState.
        else:
            return '255'
    except KeyboardInterrupt: # Catches keyboard interruption. CTRL + C, and exits.
        pass
    except:
        return '255'

# Thread1, lights LEDs.
def lightState(clientsocket):
    lock = threading.Lock()
    flag = 0        # Used for if statements, so they don't mess up the timers. 
                    # 1 means a 1 has already been received.
    deadtimer = time.time()   # Used for printing messages on screen if timer gets too great.
    lighttimer = 0.0

    # This loop runs continously. It checks the data coming from a socket and decides
    # what to do with it. If there's too long of a delay between packets, a LED will flash
    # until a packet is received. If the system receives a 1, it lights one LED and if
    # more than 5 seconds pass and the system hasn't recieved a 0, then it turns on the second LED.
    while True:
        data = listenonUDP(clientsocket) # Calls the function and returns strings. 255 == no data from socket.
        if data == '255' and time.time() - deadtimer >= D_TIME:
            lightFlash()                # Flashes light if dead timer is
        elif data == 'True' and flag == 0:
            flag = 1
            lighttimer = time.time()
            deadtimer = time.time()
            GPIO.output(7, HIGH)
        elif data == 'True' and flag == 1:
            deadtimer = time.time()
        elif data == 'False' and flag == 1:
            flag = 0
            lighttimer = time.time()
            deadtimer = time.time()
            GPIO.output(7, LOW)
            GPIO.output(11, LOW)
        elif data == 'False' and flag == 0:
            deadtimer = time.time()
        elif data == 'hello':
            deadtimer = time.time()

        if time.time() - lighttimer > 5 and flag == 1:
            GPIO.output(11, HIGH)
            

# Thread2, sends hello packets.
def sendUDP(clientsocket):
    lock = threading.Lock()
    timer = time.time()
    clientsocket.sendto(bytes('getState', MSG_ENC), (DST_IP, PORT))
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
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()  
    t2.start()

    while True:
        print('If you want to exit the program, type quit')
        data = input()
        if data == 'quit':
            GPIO.cleanup()
            clientsocket.close()
            exit()
main()
