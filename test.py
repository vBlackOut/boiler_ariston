import time
import board
import busio
import time, signal, sys, os, math
import numpy as np
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
# from terminaltables import SingleTabl
from tabulate import tabulate
import requests
import logging

#from lib.SCR import *
from lib.pwmd import PWMControl
from lib.display import *
from lib import pytuya
from datetime import datetime
from datetime import timedelta
from database import db
from numpy import mean as avg
from numpy import arange
import colored
from colored import stylize
from lib.decorator import month_decrease
sys.setrecursionlimit(10000)

PWMControl = PWMControl()

debug = False
logging.basicConfig(format='%(asctime)s %(message)s')
# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
#print(i2c.scan(), board.SDA, board.SCL)
date = datetime.now
# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

force_variable = "auto"

class Boiler_Ariston():

    def __init__(self):

        self.sonde1 = self.GetSonde1()
        self.sonde2 = self.GetSonde2()
        self.rend5 = self.rend(5)
        self.rend1 = self.rend(1, return_count=True)

    def conso_global(self):
        tuyaconso = pytuya.OutletDevice('35466753483fda783614', '192.168.1.212', 'ec83cabf1d40bc17')
        tuyaconso.set_version(3.3)
        data = tuyaconso.status()

        power = data['dps']['1']
        kwh = int(data['dps']['17'])/1000
        MilAmp = (int(data['dps']['18'])/1000)/1.2
        Watt = float(data['dps']['19'])
        Voltage = int(data['dps']['20'])/10
        VA = MilAmp*round(Voltage, 1)

        if power != True:
            tuyaconso.set_status(True, 1)

        return { 'power': power,
                 'kwh': kwh,
                 'Ampere': MilAmp,
                 'Watt': Watt,
                 'Voltage' : Voltage,
                 'VA' : VA }

    def round_of_8bit(self, number):
        float_n = float("0{}".format(str(number-int(number))[1:]))

        if number == 0 and float_n == 0.0:
            return 0
        elif float_n < 0.4:
            number = int(number)
        elif float_n >= 0.4 and float_n < 0.8:
            number = int(number)+0.5
        elif float_n >= 0.8:
            number = int(number)+1

        return number

    def GetSonde1(self):
        query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.Sonde_haut != None or db.Ballon2.Sonde_bas != None).limit(3)

        Sonde_haut = [row.Sonde_haut for row in query]
        Sonde_bas = [row.Sonde_bas for row in query]

        AvgTemp = (avg(Sonde_haut) + avg(Sonde_bas)) / 2

        if avg(Sonde_haut) <= 0 or avg(Sonde_haut) >= 70:
            pass
            #security(shutdown=True, msg="Sonde haut Ballon 1 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
            #exit(0)

        if avg(Sonde_bas) <= 0 or avg(Sonde_bas) >= 70:
            pass
            #security(shutdown=True, msg="Sonde bas Ballon 1 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
            #exit(0)


        return {"haut": {"temp": avg(Sonde_haut)}, "bas": {"temp": avg(Sonde_bas)}, "moyenne": AvgTemp}

    def GetSonde2(self):
        query = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.Sonde_haut != None or db.Ballon1.Sonde_bas != None).limit(3)
        Sonde_haut = [row.Sonde_haut for row in query]
        Sonde_bas = [row.Sonde_bas for row in query]
        AvgTemp = (avg(Sonde_haut) + avg(Sonde_bas)) / 2

        if avg(Sonde_haut) <= 0 or avg(Sonde_haut) >= 70:
            pass
            #security(shutdown=True, msg="Sonde haut Ballon 2 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
            #exit(0)

        if avg(Sonde_bas) <= 0 or avg(Sonde_bas) >= 70:
            pass
            #security(shutdown=True, msg="Sonde bas Ballon 2 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
            #exit(0)


        #return {"bas": {"temp": avg(Sonde_haut)}, "haut": {"temp": avg(Sonde_bas)}, "moyenne": AvgTemp}
        return {"bas": {"temp": avg(Sonde_haut)}, "haut": {"temp": avg(Sonde_bas)}, "moyenne": avg(Sonde_bas)}

    def security(self, shutdown=False, msg=""):

        if self.sonde2["moyenne"] > 0 and self.sonde1["moyenne"] > 0:
            if (self.sonde1['moyenne'] > 60 or self.sonde2['moyenne'] > 55):
                shutdown = True
                print("Security STOP ALL Warning temperature interne overload 50°C value is {}°C".format(self.sonde2['moyenne']))


            elif (self.sonde1['moyenne'] < 0 or self.sonde2['moyenne'] < 0):
                shutdown = True
                print("Security STOP ALL Warning temperature interne ERROR value is {EC".format(self.sonde2['moyenne']))

        if shutdown:
            print(msg)
            date = datetime.now()
            db_save = db.Ballon1.create(date=date, resistance=0, watt=0)
            db_save.save()
            db_save = db.Ballon2.create(date=date, resistance=0, watt=0)
            db_save.save()
            os.system("sudo reboot")
            exit(0)

        return None


    @month_decrease(month="Février-Septembre", decrease_percent=5, temp="temp2")
    def AjustPercent(self, temperature, temperatureMax, maxstep, temp="", test=False):

        step = round(temperatureMax - temperature, 2)

        AjustTemp = 0

        # determine la puissance de chauffe. coefficien de la temperature maximum et en fonction du rendement de chauf. ( gain de chaleur produite a l'interieur de la cuve )
        if (step > maxstep) or (step > 0 and PWMControl.angle1 > 0 and temp == "temp1") or (step > 0 and PWMControl.angle2 > 0 and temp == "temp2"):
            temperatureMax = temperatureMax # + (5 * step)
            if step > round(maxstep/0.7, 1):
                if test == False:
                    print("Boost : {} > {} {}".format(step, round(maxstep/0.7,1), temp))

                if temp == "temp1" and round((100-round(((temperatureMax/100)*temperature), 2))) > 65:
                    AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)), 2)-50

                elif temp == "temp2" and round((100-round(((temperatureMax/100)*temperature), 2))) > 60:
                    AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)), 2)-50

                elif temp == "temp2" and round((100-round(((temperatureMax/100)*temperature), 2))) > 55:
                    AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)), 2)-45

                else:
                    AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)), 2)

            else:
                if temp == "temp1" and (step <= maxstep/3):
                    if test == False:
                        print("Boost +10.8 for end {} <= {} {}".format( step, round(maxstep/3,1), temp))
                    AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)), 2)+(13/1.5)

                    if avg(self.rend5) <= 0.5:
                         AjustTemp = AjustTemp+5

                elif temp == "temp2" and (step <= maxstep/3):
                    if test == False:
                        print("Boost +10 for end {} <= {} {}".format(step, round(maxstep/3,1), temp))

                    AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)), 2)+(20/2)
                else:
                    AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)), 2)

                if AjustTemp <= 27 and AjustTemp > 10:
                    AjustTemp = AjustTemp + (3*(step/1.2))

                if AjustTemp <= 10 and step > maxstep:
                    AjustTemp = AjustTemp+12

                if AjustTemp <= 10 and step > maxstep:
                    AjustTemp = AjustTemp

                if AjustTemp <= 25 and temp == "temp1":
                    AjustTemp = AjustTemp + 3

            if temp == "temp1":
                if AjustTemp <= 33:
                    if round(avg(self.rend1[0]),3)*self.rend[1] <= 0.4:
                         if test == False:
                             print("Boost Entrer rend + ({}) rendement = {}°C".format(round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), round(round(avg(rend),3)*count_time, 3)))
                         AjustTemp = round(AjustTemp+round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), 2)


            elif temp == "temp2":
                if AjustTemp <= 30:
                    if round(avg(self.rend1[0]),3)*self.rend1[1] < 0.2:
                        if test == False:
                            print("Boost Sortie rend + ({}) rendement = {}°C".format(round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), round(round(avg(rend),3)*count_time, 3)))
                        AjustTemp = round(AjustTemp+round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), 2)

            if AjustTemp >= 100:
                AjustTemp = 99

        if force_variable == "auto":
            return round(float(AjustTemp), 2) #round_of_8bit(AjustTemp)
        elif AjustTemp > 0:
            return int(force_variable)
        else:
            return 0

    def rend(self, minute, return_count=False):
        date = datetime.now()
        date_range = date - timedelta(minutes = minute)

        query = db.Global_info.select().order_by(db.Global_info.id.desc()).where(db.Global_info.date.between(date_range, date)).where(db.Global_info.rend_ballon1 != None)
        rend = [row.rend_ballon1 for row in query]
        if return_count == False:
            return avg(rend)
        else:
            return [avg(rend), len(rend)]

    def SetResistance(self, temperature1, temperature2, test=False):

        Resistance1_P = 1500
        Resistance2_P = 1500
        Resistance1_Conso = 0
        Resistance2_Conso = 0
        Resistance2 = False
        Percent_R2 = 0
        Percent_R1 = 0
        delta = 0

        # ENTRER
        date = datetime.now()
        date_range = date + timedelta(minutes=1)

        if date.hour >= 21 or date.hour < 8:
            print("SAVE MODE >= 21 hours dans < 8 hours")

        #ENTRER
        if (temperature2 < 40 and (temperature1 >= 40)) or (temperature2 < 40 and self.sonde2["moyenne"] == 0):
            if date.hour >= 21 or date.hour < 8:
                Percent_R2 = self.AjustPercent(temperature2, 35, 10, "temp1")
            else:
                Temp_R2 = self.AjustPercent(temperature2, 40, 7, "temp1")
                if abs(temperature2-temperature1) >= 10 or Temp_R2 >= 30:
                    Percent_R2 = self.AjustPercent(temperature2, 40, 7, "temp1", test)
                else:
                    Percent_R2 = self.AjustPercent(temperature2, 35, 10, "temp1", test)

            if Percent_R2 != 0 and test == False:
                Resistance2 = True
                db_save = db.Ballon1.create(date=date, resistance=Percent_R2, watt=round((Percent_R2/100*Resistance2_P)))
                db_save.save()
                print("Resistance 1 Entrer - Turn On {} - conso: {} - {}%".format(temperature2, round(Percent_R2/100*Resistance2_P), Percent_R2))
                #PWMControl.control(1, Percent_R2)

        # SORTIE
        # SOIR R2 OFF
        if date.hour >= 21 or date.hour < 8 and Resistance2 == False:
            Percent_R1 = self.AjustPercent(temperature1, 44, 5, "temp2", test) # jusqu'a 39

        # SOIR R2 ON
        elif  date.hour >= 21 or date.hour < 8 and Resistance2 == True:
            Percent_R1 = self.AjustPercent(temperature1, 44, 5, "temp2", test) # jusqu'a 39
            if Percent_R1 > 0:
                Percent_R1 = Percent_R1-5

        # journee R2 ON
        elif (date.hour < 21 or date.hour >= 8) and Resistance2 == True:
            Percent_R1 = self.AjustPercent(temperature1, 50, 5, "temp2", test) # jusqu'a 40

        # journee R2 OFF
        elif (date.hour < 21 or date.hour >= 8) and Resistance2 == False:
            Percent_R1 = self.AjustPercent(temperature1, 55, 7, "temp2", test)

        # mise en marche
        if temperature1 < 55 and test == False:
            Resistance1 = True
            if Percent_R1 != 0:
                db_save = db.Ballon2.create(date=date, Sonde_haut=self.sonde1['haut']['temp'], Sonde_bas=self.sonde1['bas']['temp'], moyenne_temperature=temperature1, resistance=Percent_R1, watt=round((Percent_R1/100*Resistance1_P)))
                db_save.save()
                print("Resistance 2 Sortie - Turn On {} - conso: {} - {}%".format(temperature1, round(Percent_R1/100*Resistance1_P),  Percent_R1))
                #PWMControl.control(2, Percent_R1)

        return Percent_R2, Percent_R1


if __name__ == "__main__":
    boiler = Boiler_Ariston()

    boiler.security(msg="STOP FORCED")

    sonde1 = boiler.sonde1
    sonde2 = boiler.sonde2

    if debug:
        debug_table_data = [
            ['          SORTIE', '         ENTRER'],
            ["Sonde 1 - Haut {}°C ({})".format(sonde1['haut']['temp'], sonde1['haut']['resistance']), "Sonde 2 - Haut {}°C ({})".format(sonde2['haut']['temp'], sonde2['haut']['resistance'])],
            ["Avg Temp Sonde 1: {}°C".format(round(sonde1['moyenne'], 1)), "Avg temp Sonde 2: {}°C".format(round(sonde2['moyenne'], 1))],
            ["Sonde 1 - Bas {}°C ({})".format(sonde1['bas']['temp'], sonde1['bas']['resistance']), "Sonde 2 - Bas {}°C ({})".format(sonde2['bas']['temp'], sonde2['bas']['resistance'])]
        ]
        debug_table = AsciiTable(debug_table_data)
        print(debug_table.table)

    else:

        moyenne = round((round(sonde1['moyenne'],1) + round(sonde2['moyenne'],1)) / 2,1)
        nb_moyenne = round((round(sonde2['moyenne'],1) - round(sonde1['moyenne'],1)),1)

        table_data = [
            ["Sonde 1: {}°C".format(round(sonde1['moyenne'], 1)), "{}°C ({})".format(moyenne, nb_moyenne), "Sonde 2: {}°C".format(round(sonde2['moyenne'], 1))],
        ]
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        table = tabulate(table_data, headers=["SORTIE","<---------", "ENTRER"], tablefmt="pretty")
        print('*{}Chauf Eau 2.0   {}       *'.format(" "*10, dt_string))
        print(table)

        R1, R2 = boiler.SetResistance(round(sonde1['moyenne'], 1), round(sonde2['moyenne'], 1))

        if R1 == 0:
            db_save = db.Ballon1.create(date=date, resistance=0, watt=0)
            db_save.save()

        if R2 == 0:
            db_save = db.Ballon2.create(date=date, resistance=0, watt=0)
            db_save.save()

    print()
    exit(0)
