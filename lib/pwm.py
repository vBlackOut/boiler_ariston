#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIOi
import numpy as np
import time
import os, sys
from daemonize import Daemonize
sys.path.append("..")
from database import db
from lib.daemon import *
from random import uniform
class PWMControl():

    def __init__(self):

        self.servo_pin_1 = 18  # équivalent de GPIO 18
        self.servo_pin_2 = 19  # équivalent de GPIO 19

        GPIO.setmode(GPIO.BCM)  # notation BCM
        GPIO.setwarnings(False)
        GPIO.setup(self.servo_pin_1, GPIO.OUT)  # pin configurée en sortie
        GPIO.setup(self.servo_pin_2, GPIO.OUT)  # pin configurée en sortie

        # 26 hZ en dessous de 20 %
        self.pwm1 = GPIO.PWM(self.servo_pin_1, 0.975)  # pwm à une fréquence de 50 Hz
        self.pwm2 = GPIO.PWM(self.servo_pin_2, 0.975)  # pwm à une fréquence de 50 Hz

        self.pwm1.start(100)
        self.pwm2.start(100)

        angle1 = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.resistance != None).limit(1)
        angle1 = [row.resistance for row in angle1]

        angle2 = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.resistance != None).limit(1)
        angle2 = [row.resistance for row in angle2]

        self.angle1 = angle1[0]
        self.angle2 = angle2[0]
        #super().__init__(pidfile=self.pidfile, sysargv=self.sysargv, stderr=self.stderr, stdout=self.stdout)

    def updateAngle(self):
        angle1 = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.resistance != None).limit(1)
        angle1 = [row.resistance for row in angle1]

        angle2 = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.resistance != None).limit(1)
        angle2 = [row.resistance for row in angle2]

        self.angle1 = angle1[0]
        self.angle2 = angle2[0]

    def control(self, percent1, percent2):
        regresif1 = round(float(percent1)/2, 2)
        regresif2 = round(float(percent2)/2, 2)

        if percent1 == 100:
            percent1 = 99.99

        if percent2 == 100:
            percent2 = 99.99

        percent1 = abs(float(percent1) - 100)
        percent2 = abs(float(percent2) - 100)

        if percent1 != self.angle1:
            if percent1 == 0:
                self.pwm1.stop()

            if percent1 == 0 and self.angle2 == 0:
                self.pwm2.stop()
                self.pwm1.stop()
            else:
                self.pwm1.ChangeDutyCycle(percent1+regresif1)


        if percent2 != self.angle2:
            if percent2 == 0:
                self.pwm2.stop()

            if percent2 == 0 and self.angle1 == 0:
                self.pwm2.stop()
                self.pwm1.stop()
            else:
                self.pwm2.ChangeDutyCycle(percent2+regresif2)

        return percent1, percent2

    def run(self):
        while True:
            self.updateAngle()
            #value = uniform(1.0, 10.0)
            self.control(self.angle1, self.angle2)
            time.sleep(0.5)

    def Reset(self):
        GPIO.cleanup()
        return True

if __name__ == "__main__":
    pwm = PWMControl()
    pwm.run()
