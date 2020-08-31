#!/usr/bin/env python

import signal
import time
import sys
import socket
import board
from threading import Thread
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

ip_address = "127.0.0.1"
port = 6902
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((ip_address,port))
sock.listen()
ok = 1 

reader = SimpleMFRC522()



try:
        id, text = reader.read()
        print(id)
        print(text)
finally:
        GPIO.cleanup()