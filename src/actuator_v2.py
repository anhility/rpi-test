# USE ON RASPBERRY PI

import socket
import RPi.GPIO as GPIO
import threading
import time

# Pin voltage
HIGH = GPIO.HIGH
LOW = GPIO.LOW

# Networking
SRC_IP = '10.35.0.1' # The actuator.
DST_IP = '10.34.0.1' # The sensor.
PORT = 5005 # Port number used for sending and listening.

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
# If if it fails, or the received IP doesn't match the sensor's IP, it returns '255'.
def listenonUDP(clientsocket):
    lock = threading.Lock()
    try:
        lock.acquire()
        data, (address, port) = clientsocket.recvfrom(1024)
        lock.release()
        if str(address) == DST_IP and int(port) == PORT: # checks for correct IP and PORT.
            return data.decode(MSG_ENC) # return decoded data for use in the function lightState.
        else:
            return '255'
    except KeyboardInterrupt: # Catches keyboard interruption. CTRL + C, and exits.
        pass
    except:
        return '255'

# Thread1, lights LEDs. It uses the 'listenonUDP'-function to determine whether or not to turn on
# the LEDs. If it the string in the variable data matches 'True', it will turn on the LED according to the
# specifications. It it receives 'False', it will turn off the LEDs.
# If it receives a 'hello', it will update the dead timer. Every other string or data is disregarded.
def lightState(clientsocket):
    lock = threading.Lock()
    flag = 0        # Used for if statements, so they don't reset the timer if multiple packets containing the
                    # same data is received. 1 means 'True' has already been received, 0 for 'False'.
    deadtimer = time.time()   # Used for printing messages on screen if timer gets too great.
    lighttimer = 0.0 # Used for determining when to light the second LED.

    while True:
        data = listenonUDP(clientsocket) # Calls the function and returns strings. 255 == no data from socket.
        if data == '255' and time.time() - deadtimer >= D_TIME:
            lightFlash()                # Flashes light if dead timer is over threshold.
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
    lock = threading.Lock() # Used for locking the sockets later. Prevents cancelling by the operating system.
    timer = time.time() # used for sending packets containing the string 'hello' within intervals.
    clientsocket.sendto(bytes('getState', MSG_ENC), (DST_IP, PORT))
    while True:
        if time.time() - timer >= 0.5:
            lock.acquire() # lock socket.
            clientsocket.sendto(bytes(SNT_MSG, MSG_ENC), (DST_IP, PORT))
            lock.release() # unlock socket.
            timer = time.time() # Resets timer.

def main():
    print('Running program')
    GPIO.setmode(GPIO.BOARD)        # Sets pin mode to BOARD (Pin numbers)
    GPIO.setwarnings(False)         # Suppresses startup warnings.
    GPIO.setup(7, GPIO.OUT)         # Sets pins as output.
    GPIO.setup(11, GPIO.OUT)
    GPIO.output(7, LOW)             # Turns off lights at startup
    GPIO.output(11, LOW)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsocket.bind((SRC_IP, PORT))   # Binds the IP and port to the pi. Prevents the socket from closing.
    clientsocket.setblocking(False)     # Prevents wait time when reading from socket. 
                                        # That way, the socket always times out when there's no data to be read.

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
        try:
            data = input()
            if data == 'quit':
                GPIO.cleanup()
                clientsocket.close()
                exit()
        except KeyboardInterrupt:
            GPIO.cleanup()
            clientsocket.close()
            exit()
        except EOFError:
            GPIO.cleanup()
            clientsocket.close()
            exit()
main()
