#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import numpy as np
import time

servo_pin_1 = 18  # équivalent de GPIO 18
servo_pin_2 = 19  # équivalent de GPIO 18

GPIO.setmode(GPIO.BCM)  # notation BCM
GPIO.setwarnings(False)
GPIO.setup(servo_pin_1, GPIO.OUT)  # pin configurée en sortie
GPIO.setup(servo_pin_2, GPIO.OUT)  # pin configurée en sortie

# 26 hZ en dessous de 20 %
pwm1 = GPIO.PWM(servo_pin_1, 0.975)  # pwm à une fréquence de 50 Hz
pwm2 = GPIO.PWM(servo_pin_2, 0.975)  # pwm à une fréquence de 50 Hz

pwm1.start(100)
pwm2.start(100)

# duty = 80.0
#pwm1.ChangeDutyCycle(10)
try:
    while True:
        dcstart = input("dutycycle : ")

        dc = abs(float(dcstart) - 100)
        dcpercent = (float(dcstart) * 1500)/100
        dc_percent_phy = dcpercent*1.8

        regresif = round(float(dcstart)/2, 2)

        print("percent {} percent_real {} {}".format(dcpercent, dc_percent_phy, regresif))

        if dc == 100:
            print("stop")
            pwm1.stop()
            #pwm2.stop()
            GPIO.cleanup()
        print(abs(float(dc)+regresif))
        pwm1.ChangeDutyCycle(abs(float(dc)+regresif))
        #time.sleep(1)
except KeyboardInterrupt:
        print("stop")
        pwm1.stop()
        #pwm2.stop()
        GPIO.cleanup()
