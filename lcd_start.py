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
from numpy import mean as avg
from lib.daemon import *
from database import db
import smbus
from w1thermsensor import W1ThermSensor
import RPi.GPIO as GPIO

libdir = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(libdir):
    sys.path.append(libdir)

# scr = SCR.SCR(dev = "/dev/ttySC0",data_mode = 1)
debug = False
logging.basicConfig(format='%(asctime)s %(message)s')
# Create the I2C bus

class LCD_DISPLAY(Daemon):
        def __init__(self):

            # lcd_device = lcd()
            # lcd_device.lcd_clear()

            self.pidfile = "/tmp/daemon-lcd_python.pid"
            self.sysargv = sys.argv
            self.stderr = "/tmp/error.log"
            self.stdout = "/tmp/outlcd.log"
            self.blockscreen = False

            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(self.i2c)
            self.ResistanceValue = self.convert("10k")
            self.Pin_FlowSensor = 21
            # GPIO.setup(self.Pin_FlowSensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            # GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.RISING, callback=self.fct_decompte)

            self.buttonMenu = 18
            self.buttonPlus = 17
            self.buttonMoins = 19

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.buttonMenu, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # menu
            GPIO.setup(self.buttonPlus, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # +
            GPIO.setup(self.buttonMoins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # -

            # self.buttonPlus = 17
            # self.buttonMin = 19
            #GPIO.cleanup()
            self.pulseCount = 0
            self.tdelta = 0
            self.calibrationFactor = 553
            self.time_start = time.time() # en secondes
            self.flowlitretotal = 0
            self.pulsecountstotal  = 0
            self.pos = None
            self.count_lcd = 0
            self.time_start = time.time() # en secondes
            self.count_failling = 0
            self.time_push = datetime.now()
            super().__init__(pidfile=self.pidfile, sysargv=self.sysargv, stderr=self.stderr, stdout=self.stdout)

            # GPIO.setup(self.buttonMenu, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # +
            # GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # -

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
                flow = (self.pulseCount / self.calibrationFactor) / (tdelta * 60)
                flow = round(flow, 2)
                flowLitre = (self.pulseCount / self.calibrationFactor)
                self.flowlitretotal += flowLitre
                self.pulsecountstotal += self.pulseCount
                #print(flow, self.pulseflow)
                # ecriture de donnees dans le fichier
                # fichier = open("/home/pi/mesuresDebit.log", "a")
                # fichier.write("%s,%s,%s,%s\n" % (time.strftime('%a %H:%M:%S'), flow, temperature, humidity))
                # fichier.close()
                #rend1, rend2 = self.rendement(30, save=False)
                # if rend2 < 0:
                date = datetime.now
                db_save = db.Global_info.create(date=date, flow=round(self.pulseCount, 2))
                db_save.save()

                # traces a l ecran
                print(time.asctime(time.localtime(time.time())),' debit : ', flow, 'l/min ', self.pulseCount, " counts ", round(self.flowlitretotal,2), "F/L" )
                # Remise a zero
                self.reset_flow()

        def reset_flow(self):
            self.tdelta = 0
            self.pulseCount = 0
            self.time_start = time.time()

        def run(self):
            GPIO.setup(self.Pin_FlowSensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.Pin_FlowSensor, GPIO.RISING, callback=self.fct_decompte)

            count = 0
            count_2 = 0

            # GPIO.add_event_detect(self.buttonMenu, GPIO.RISING)  # Menu/Select
            # GPIO.add_event_detect(self.buttonPlus, GPIO.RISING)  # +
            # GPIO.add_event_detect(self.buttonMoins, GPIO.RISING) # -

            while True:
                # if count >= 1:
                #     self.date_now_failling = datetime.now()

                #self.detectbutton()
                self.sonde1 = self.GetSonde1()
                self.sonde2 = self.GetSonde2()

                if self.blockscreen == False:
                    #self.detectbutton()
                    try:
                        self.write_lcd(temp1=round(self.sonde1['moyenne'], 1), temp2=round(self.sonde2['moyenne'], 1))
                    except:
                        pass
                    time.sleep(0.2)

                if datetime.now().hour > 22 or datetime.now().hour < 6:
                    self.set_lcd_light("lcd", 80) # 40

                elif datetime.now().hour >= 6 or datetime.now().hour < 12:
                    self.set_lcd_light("lcd", 27)

                elif datetime.now().hour >= 12:
                    self.set_lcd_light("lcd", 15)

                time.sleep(0.2)

                date = datetime.now
                if count >= 10:
                    count = 0
                    db_save = db.Ballon1.create(date=date, Sonde_haut=self.sonde2['haut']['temp'], Sonde_bas=self.sonde2['bas']['temp'], moyenne_temperature=self.sonde2['moyenne'])
                    db_save.save()

                    db_save = db.Ballon2.create(date=date, Sonde_haut=self.sonde1['haut']['temp'], Sonde_bas=self.sonde1['bas']['temp'], moyenne_temperature=self.sonde1['moyenne'])
                    db_save.save()

                    self.rendement(30, save=True)

                # if count_2 >= 10:
                #     count_2 = 0
                #     try:
                #         sensor = W1ThermSensor()
                #         db_save = db.Global_info.create(date=date, sonde_interne=round(sensor.get_temperature(),2))
                #         db_save.save()
                #     except:
                #         pass

                # count_2 = count_2 +1
                count = count + 1
                #self.detectbutton()

        def detectbutton(self):

            if GPIO.event_detected(self.buttonMenu):
                self.last = self.time_push
                self.time_push = datetime.now()
                date = self.time_push - self.last
                print("button menu {} {}".format(date.seconds, date.microseconds))

                if date.seconds == 0 and date.microseconds <= 1000:
                    self.count_failling = self.count_failling + 1

                if self.count_failling >= 1:
                    lcd_device = lcd()
                    lcd_device.lcd_clear()
                    lcd_device.lcd_display_string("       MODE   ", 1)
                    lcd_device.lcd_display_string("        SECURITER".format(self.pos), 2)
                    time.sleep(15)
                    self.count_failling = 0
                    return 0

                elif self.pos == None:
                    self.pos = 0
                    self.buttonMenucall()

            if GPIO.event_detected(self.buttonPlus):
                self.last = self.time_push
                self.time_push = datetime.now()
                date = self.time_push - self.last
                print("button plus {} {}".format(date.seconds, date.microseconds))
                if date.seconds == 0 and date.microseconds <= 1000:
                    self.count_failling = self.count_failling + 1

                if self.count_failling >= 1:
                    lcd_device = lcd()
                    lcd_device.lcd_clear()
                    lcd_device.lcd_display_string("       MODE   ", 1)
                    lcd_device.lcd_display_string("        SECURITER".format(self.pos), 2)
                    time.sleep(15)
                    self.count_failling = 0
                    return 0

                elif self.pos != None:
                    self.pos = self.pos + 1
                    self.write_lcd(menu=True)
                    self.count_lcd = 0

            if GPIO.event_detected(self.buttonMoins):
                self.last = self.time_push
                self.time_push = datetime.now()
                date =  self.time_push - self.last
                print("button moins {} {}".format(date.seconds, date.microseconds))

                if date.seconds == 0 and date.microseconds <= 1000:
                    self.count_failling = self.count_failling + 1

                if self.count_failling >= 1:
                    lcd_device = lcd()
                    lcd_device.lcd_clear()
                    lcd_device.lcd_display_string("       MODE   ", 1)
                    lcd_device.lcd_display_string("        SECURITER".format(self.pos), 2)
                    time.sleep(15)
                    self.count_failling = 0
                    return 0

                elif self.pos != None:
                    self.pos = self.pos - 1
                    self.write_lcd(menu=True)
                    self.count_lcd = 0


        def buttonMenucall(self):
            # if touch button Menu select option button
            if self.blockscreen == True:
                return 0
                #if self.pos == 1:
            else:
                self.blockscreen = True

                self.write_lcd(menu=True)
                self.max_count = 10
                self.count_lcd = 0

                while True:
                    if self.count_lcd == self.max_count or self.blockscreen == False:
                        self.count_lcd = 0
                        break
                    self.detectbutton()
                    time.sleep(1)
                    self.count_lcd = self.count_lcd + 1

                # GPIO.remove_event_detect(self.buttonPlus)
                # GPIO.remove_event_detect(self.buttonMoins)
                # GPIO.remove_event_detect(self.buttonMenu)

                lcd_device = lcd()
                lcd_device.lcd_clear()
                self.blockscreen = False
                self.write_lcd(temp1=round(self.sonde1['moyenne'], 1), temp2=round(self.sonde2['moyenne'], 1))
                self.pos = None

        def set_lcd_light(self, channel, value):
            bus = smbus.SMBus(1)
            if channel == "lcd":
                data_now_channel1 = bus.read_byte_data(0x2C, 0x01)
                if data_now_channel1 != value:
                    # bus1
                    bus.write_i2c_block_data(0x2C, 0x01, [value])
                    time.sleep(0.2)

            if channel == "fan":
                data_now_channel2 = bus.read_byte_data(0x2C, 0x03)
                if data_now_channel2 != value:
                    # bus2
                    bus.write_i2c_block_data(0x2C, 0x03, [value])
                    time.sleep(0.2)

        def convert(self, value):
            if value:
                # determine multiplier
                multiplier = 1
                if value.endswith('K') or value.endswith('k'):
                    multiplier = 1000
                    value = value[0:len(value)-1] # strip multiplier character
                elif value.endswith('M') or value.endswith('m'):
                    multiplier = 1000000
                    value = value[0:len(value)-1] # strip multiplier character

                # convert value to float, multiply, then convert the result to int
                return int(float(value) * multiplier)

            else:
                return 0

        def write_lcd(self, **kwargs):

            # lcd start
            lcd_device = lcd()
            try:
                # if kwargs['reset'] == True:
                #     lcd_device.lcd_clear()
                if self.pos is not None and self.pos < 0:
                    self.pos = 0

                if kwargs['menu'] == True:
                    if self.pos == 0:
                        lcd_device.lcd_clear()
                        lcd_device.lcd_display_string("       MENU   ", 1)
                        lcd_device.lcd_display_string("        {}       -> ".format(self.pos), 2)
                        lcd_device.lcd_display_string("    Temperature   ", 3)
                        lcd_device.lcd_display_string("   Ballon droite",4)

                    elif self.pos == 1:
                        lcd_device.lcd_clear()
                        lcd_device.lcd_display_string("       MENU   ", 1)
                        lcd_device.lcd_display_string("  <-    {}       -> ".format(self.pos), 2)
                        lcd_device.lcd_display_string("    Temperature   ", 3)
                        lcd_device.lcd_display_string("   Ballon gauche",4)
                    else:
                        lcd_device.lcd_clear()
                        lcd_device.lcd_display_string("       MENU   ", 1)
                        lcd_device.lcd_display_string("  <-     {}      -> ".format(self.pos), 2)
                        lcd_device.lcd_display_string("", 3)
                        lcd_device.lcd_display_string("",4)
            except KeyError:
                pass

            try:
                lineTemperature = ""
                medium = (kwargs['temp2'] + kwargs['temp1']) / 2
                date = datetime.now().strftime('%d, %b %Y %H:%M')
                for key, value in kwargs.items():

                    if key == "temp1":
                        lineTemperature += "{}C".format(round(value,1))

                    if key == "temp2":
                        lineTemperature += "  <----   {}C".format(round(value,1))

                # now we can display some characters (text, line)
                lcd_device.lcd_display_string(" {}".format(date), 1)
                lcd_device.lcd_display_string(lineTemperature, 3)
                lcd_device.lcd_display_string("       {}C".format(round(medium,1)), 4)
            except KeyError:
                pass

        def calcResistance(self, voltage):
            return ((self.ResistanceValue * voltage) / (3.3 - voltage))

        def calcTemp(self, resistance):
            # default return 1 / ( (math.log(resistance / self.ResistanceValue) / 3453) + (1 / (273.15+25)) ) - 273.15;
            ## 3380 pour 50°C
            ## 3422 pour 75°C
            ## 3435 pour 85°C
            ## 3453 pour 100°C
            return 1 / ((math.log(resistance / self.ResistanceValue) / 3453) + (1 / (273.15+25)) ) - 273.15;

        def GetSonde1(self):
            etalonne = 1.5
            chan0 = AnalogIn(self.ads, ADS.P0)
            R0 = self.calcResistance(chan0.voltage)
            Temp0 = round(self.calcTemp(R0), 2) + etalonne

            chan1 = AnalogIn(self.ads, ADS.P1)
            R1 = self.calcResistance(chan1.voltage)
            Temp1 = round(self.calcTemp(R1), 2) + etalonne
            try:
                AvgTemp = (Temp0 + Temp1) / 2
            except:
                AvgTemp = -1

            return {"haut": {"temp": Temp0, "resistance": round(R0)}, "bas": {"temp": Temp1, "resistance": round(R1)}, "moyenne": AvgTemp}

        def rendement(self, minute, save=True):
            date = datetime.now()
            date_range = date - timedelta(seconds = minute)

            query = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.date.between(date_range, date))
            Sonde = [row.moyenne_temperature for row in query if row.moyenne_temperature != None and row.date != None or row.moyenne_temperature != None and row.date != None]
            if (Sonde[-1]-avg(Sonde) <= 0):
                Sonde_rend1 = (max(Sonde) - min(Sonde)) / minute
            else:
                Sonde_rend1 = -(max(Sonde) - min(Sonde)) / minute
            # if round(Sonde_rend1*60,2) < 7:
            #     print("Estimation Ballon 1 Entrer : -{}°C par heures".format(round(Sonde_rend1*60,2)))
            # else:
            #     print("Estimation Ballon 1 Entrer : Calcule en cours...".format(round(Sonde_rend1*60,2)))

            query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.date.between(date_range, date))
            Sonde = [row.moyenne_temperature for row in query if row.moyenne_temperature != None and row.date != None or row.moyenne_temperature != None and row.date != None]
            if (Sonde[-1]-avg(Sonde) <= 0):
                Sonde_rend2 = (max(Sonde) - min(Sonde)) / minute
            else:
                Sonde_rend2 = -(max(Sonde) - min(Sonde)) / minute
            # if round(Sonde_rend2*60,2) < 7:
            #     print("Estimation Ballon 2 Sortie: -{}°C par heures\n".format(round(Sonde_rend2*60,2)))
            # else:
            #     print("Estimation Ballon 2 Sortie: Calcule en cours...\n".format(round(Sonde_rend2*60,2)))
            if save == True:
                db_save = db.Global_info.create(rend_ballon1=Sonde_rend1 * minute, rend_ballon2=Sonde_rend2 * minute, date=date)
                db_save.save()

            return Sonde_rend1, Sonde_rend2


        def GetSonde2(self):
            etalonne = 1.5
            chan2 = AnalogIn(self.ads, ADS.P3)
            R2 = self.calcResistance(chan2.voltage)
            Temp2 = round(self.calcTemp(R2), 2) + etalonne

            chan3 = AnalogIn(self.ads, ADS.P2)
            R3 = self.calcResistance(chan3.voltage)
            Temp3 = round(self.calcTemp(R3), 2) + etalonne
            try:
                AvgTemp = (Temp2 + Temp3) / 2
            except:
                AvgTemp = -1

            return {"bas": {"temp": Temp3, "resistance": round(R2)}, "haut": {"temp": Temp2, "resistance": round(R3)}, "moyenne": AvgTemp}

if __name__ == "__main__":
    daemon = LCD_DISPLAY()
    #print(daemon.run())
