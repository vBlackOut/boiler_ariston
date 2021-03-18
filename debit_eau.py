import time
import board
import busio
import time, signal, sys, os, math
import numpy as np
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from terminaltables import SingleTable
import requests
import logging
from lib.SCR import *
from lib.display import *
from datetime import datetime
from datetime import timedelta
from lib.daemon import *
from database import db
import smbus
from w1thermsensor import W1ThermSensor
import RPi.GPIO as GPIO

libdir = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(libdir):
    sys.path.append(libdir)

debug = False
logging.basicConfig(format='%(asctime)s %(message)s')

class Flow_sensor(Daemon):
        def __init__(self):

            self.pidfile = "/tmp/daemon-flow_sensor_python.pid"
            self.sysargv = sys.argv

            self.Pin_FlowSensor = 21
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.Pin_FlowSensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

            self.pulseCount = 0
            self.tdelta = 0
            self.calibrationFactor = 553
            self.time_start = time.time() # en secondes
            self.flowlitretotal = 0
            self.pulsecountstotal  = 0
            #GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.BOTH, callback=self.fct_decompte, bouncetime=1)
            GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.RISING, callback=self.fct_decompte)

            #super().__init__(pidfile=self.pidfile, sysargv=self.sysargv)

        # ----------------------------------------------------------
        # function pour le callback de l'evenement du FlowSensor.
        # Lorsque le FlowSensor va tourner, on va enregistrer les
        # donnees.
        def fct_decompte(self, channel):
            self.pulseCount += 1

            # Enregistrement des donnees toutes les 2 secondes
            self.tdelta = (time.time() - self.time_start)
            if self.tdelta  >= 2:
               # Calcul du flux
                flow = (self.pulseCount / self.calibrationFactor) / (self.tdelta * 60)
                flow = round(flow, 2)
                flowLitre = (self.pulseCount / self.calibrationFactor)
                if self.pulseCount > 101:
                    self.flowlitretotal += flowLitre
                    self.pulsecountstotal += self.pulseCount
                #print(flow, self.pulseflow)
                # ecriture de donnees dans le fichier
                # fichier = open("/home/pi/mesuresDebit.log", "a")
                # fichier.write("%s,%s,%s,%s\n" % (time.strftime('%a %H:%M:%S'), flow, temperature, humidity))
                # fichier.close()

                # traces a l ecran
                date = datetime.now
                db_save = db.Global_info.create(date=date, flow=round(self.pulseCount, 2))
                print(time.asctime(time.localtime(time.time())),' debit : ', flow, 'l/min ', self.pulseCount, " counts ", round(self.flowlitretotal,2), "F/L" )
                # Remise a zero
                self.reset_flow()

        def reset_flow(self):
            self.tdelta = 0
            self.pulseCount = 0
            self.time_start = time.time()
            # GPIO.remove_event_detect(self.Pin_FlowSensor)
            # GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.RISING, callback=self.fct_decompte)
            # GPIO.setup(self.Pin_FlowSensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)



        def run(self):
            #GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.BOTH, callback=self.fct_decompte)

            while True:
                #~GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.BOTH, callback=self.fct_decompte)
                time.sleep(0.1)

if __name__ == "__main__":
    daemon = Flow_sensor()
    daemon.run()
