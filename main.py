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

def conso_global():
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

def convert(value):
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

ResistanceValue = convert("10k")

def round_of_8bit(number):
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

def calcResistance(voltage):
    return ((ResistanceValue * voltage) / (3.3 - voltage))

def calcTemp(resistance):
    return 1 / ( (math.log(resistance / ResistanceValue) / 3435) + (1 / (273.15+25)) ) - 273.15;

def security(shutdown=False, msg=""):

    sonde1 = GetSonde1()
    sonde2 = GetSonde2()

    if sonde1['moyenne'] > 80 or sonde2['moyenne'] > 80:
        shutdown = True
    elif sonde1['moyenne'] < 0 or sonde2['moyenne'] < 0:
        shutdown = True

    query = db.Global_info.select().order_by(db.Global_info.id.desc()).where(db.Global_info.sonde_interne != None).limit(1)
    Sonde_interne = [row.sonde_interne for row in query]
    Sonde_interne_date = [row.date for row in query]

    Avg_sonde_interne = avg(Sonde_interne)

    now  = datetime.now()
    try:
        duration = now - Sonde_interne_date[-1]
        duration_in_s = duration.total_seconds()
    except IndexError:
        PWMControl.control(1, 0)
        PWMControl.control(2, 0)
        print("Security STOP ALL Warning temperature interne ERROR value is {}°C".format(Avg_sonde_interne))
        exit(0)

    if Avg_sonde_interne >= 50:
        PWMControl.control(1, 0)
        PWMControl.control(2, 0)
        print("Security STOP ALL Warning temperature interne overload 50°C value is {}°C".format(Avg_sonde_interne))
        lcd_device = lcd()
        lcd_device.lcd_clear()
        date = datetime.now().strftime('%d, %b %Y %H:%M')
        lcd_device.lcd_display_string(" {}".format(date), 1)
        lcd_device.lcd_display_string("Error System Temp. interne".format(self.pos), 2)
        exit(0)

    # elif duration_in_s >= 120:
    #     channelVoltage(1, 0, disable=True)
    #     channelVoltage(2, 0, disable=True)
    #     print("Security no possible to check recent value temperature system... last: {}s [{}]".format(round(duration_in_s), stylize("ERROR", colored.fg("red"))))
    #     lcd_device = lcd()
    #     lcd_device.lcd_clear()
    #     date = datetime.now().strftime('%d, %b %Y %H:%M')
    #     lcd_device.lcd_display_string(" {}".format(date), 1)
    #     lcd_device.lcd_display_string("System Temp. interne".format(self.pos), 2)
    #     lcd_device.lcd_display_string("last: {}s [{}]".format(round(duration_in_s), "ERROR"), 3)
    #     exit(0)

    # else:
    #     print("\nSystem check temperature ... {}°C last: {}s [{}] \n".format(Avg_sonde_interne, round(duration_in_s), stylize("OK", colored.fg("green"))))

    if shutdown:
        print(msg)
        PWMControl.control(1, 0)
        PWMControl.control(2, 0)
        exit(0)

def GetSonde1():
    #db.Ballon2()
    #db.Ballon1.select().order_by(db.Ballon1.id.desc()).get()
    query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.Sonde_haut != None or db.Ballon2.Sonde_bas != None).limit(1)
    #print(query[0].date)
    Sonde_haut = [row.Sonde_haut for row in query]
    Sonde_bas = [row.Sonde_bas for row in query]
    AvgTemp = (avg(Sonde_haut) + avg(Sonde_bas)) / 2
    if avg(Sonde_haut) <= 0 or avg(Sonde_haut) >= 70:
        #pass
        security(shutdown=True, msg="Sonde haut Ballon 1 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
        exit(0)

    if avg(Sonde_bas) <= 0 or avg(Sonde_bas) >= 70:
        #pass
        security(shutdown=True, msg="Sonde bas Ballon 1 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
        exit(0)
    # etalonne = 1.5
    # chan0 = AnalogIn(ads, ADS.P0)
    # R0 = calcResistance(chan0.voltage)
    # Temp0 = round(calcTemp(R0), 1) + etalonne
    #
    # chan1 = AnalogIn(ads, ADS.P1)
    # R1 = calcResistance(chan1.voltage)
    # Temp1 = round(calcTemp(R1), 1) + etalonne
    # AvgTemp = (Temp0 + Temp1) / 2

    return {"haut": {"temp": avg(Sonde_haut)}, "bas": {"temp": avg(Sonde_bas)}, "moyenne": AvgTemp}

def GetSonde2():
    query = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.Sonde_haut != None or db.Ballon1.Sonde_bas != None).limit(1)
    Sonde_haut = [row.Sonde_haut for row in query]
    Sonde_bas = [row.Sonde_bas for row in query]
    AvgTemp = (avg(Sonde_haut) + avg(Sonde_bas)) / 2

    if avg(Sonde_haut) <= 0 or avg(Sonde_haut) >= 70:
        #pass
        security(shutdown=True, msg="Sonde haut Ballon 2 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
        exit(0)

    if avg(Sonde_bas) <= 0 or avg(Sonde_bas) >= 70:
        #pass
        security(shutdown=True, msg="Sonde bas Ballon 2 value {} [{}] min 1, max 70".format(Sonde_haut, stylize("ERROR", colored.fg("red"))))
        exit(0)

    # etalonne = 1.5
    # chan2 = AnalogIn(ads, ADS.P3)
    # R2 = calcResistance(chan2.voltage)
    # Temp2 = round(calcTemp(R2), 1) + etalonne
    #
    # chan3 = AnalogIn(ads, ADS.P2)
    # R3 = calcResistance(chan3.voltage)
    # Temp3 = round(calcTemp(R3), 1) + etalonne
    # AvgTemp = (Temp2 + Temp3) / 2

    return {"bas": {"temp": avg(Sonde_haut)}, "haut": {"temp": avg(Sonde_bas)}, "moyenne": AvgTemp}
    #return {"bas": {"temp": avg(Sonde_haut)}, "haut": {"temp": avg(Sonde_bas)}, "moyenne": avg(Sonde_bas)}

@month_decrease(month="Février-Septembre", decrease_percent=5, temp="temp2")
def AjustPercent(temperature, temperatureMax, maxstep, temp=""):
    #print(temperature, temperatureMax)
    #PWMControl = PWMControl()
    step = round(temperatureMax - temperature, 2)

    AjustTemp = 0

    #print(step, maxstep, temp, scr.angle2, scr.angle1)
    # determine la puissance de chauffe. coefficien de la temperature maximum et en fonction du rendement de chauf. ( gain de chaleur produite a l'interieur de la cuve )
    if (step > maxstep) or (step > 0 and PWMControl.angle1 > 0 and temp == "temp1") or (step > 0 and PWMControl.angle2 > 0 and temp == "temp2"):
        temperatureMax = temperatureMax # + (5 * step)
        if step > round(maxstep/0.7 ,1):

            print("Boost : {} > {} {}".format(step, round(maxstep/0.7,1), temp))

            if temp == "temp1" and round((100-round(((temperatureMax/100)*temperature), 2))) > 65:
                AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)))-50

            elif temp == "temp2" and round((100-round(((temperatureMax/100)*temperature), 2))) > 60:
                AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)))-50

            elif temp == "temp2" and round((100-round(((temperatureMax/100)*temperature), 2))) > 55:
                AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)))-45

            else:
                AjustTemp = round((100-round(((temperatureMax/100)*temperature), 2)))

        else:
            if temp == "temp1" and (step <= maxstep/3):
                print("Boost +10.8 for end {} <= {} {}".format( step, round(maxstep/3,1), temp))
                AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)))+(13/1.5)

                # minute = 30
                # date_rend = datetime.now()
                # date_range = date_rend + timedelta(minutes = minute)
                #
                # query = db.Global_info.select().where(db.Global_info.date.between(date_rend, date_range)).where(db.Global_info.rend_ballon1 != None)
                # print(query)
                # rend = [row.rend_ballon1 for row in query]
                # print(rend)

                minute = 5
                date = datetime.now()
                date_range = date - timedelta(minutes = minute)

                query = db.Global_info.select().order_by(db.Global_info.id.desc()).where(db.Global_info.date.between(date_range, date)).where(db.Global_info.rend_ballon1 != None)
                rend = [row.rend_ballon1 for row in query]
                if avg(rend) <= 0.5:
                     AjustTemp = AjustTemp+5

            elif temp == "temp2" and (step <= maxstep/3):
                print("Boost +10 for end {} <= {} {}".format(step, round(maxstep/3,1), temp))
                AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)))+(20/2)
            else:
                AjustTemp = round(100-(100-round(((temperatureMax/100)*temperature), 2)))

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
                minute = 1
                date = datetime.now()
                date_range = date - timedelta(minutes = minute)

                query = db.Global_info.select().order_by(db.Global_info.id.desc()).where(db.Global_info.date.between(date_range, date)).where(db.Global_info.rend_ballon1 != None)
                rend = [row.rend_ballon1 for row in query]
                count_time = len(rend)
                #print(round(avg(rend),3), count_time, round(avg(rend),3)*count_time, round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2))
                # print(arange(0.1, 0.6, 0.1))
                if round(avg(rend),3)*count_time <= 0.4:
                     print("Boost Entrer rend + ({}) rendement = {}°C".format(round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), round(round(avg(rend),3)*count_time, 3)))
                     AjustTemp = round(AjustTemp+round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2))


        elif temp == "temp2":
            if AjustTemp <= 30:
                minute = 1
                date = datetime.now()
                date_range = date - timedelta(minutes = minute)

                query = db.Global_info.select().order_by(db.Global_info.id.desc()).where(db.Global_info.date.between(date_range, date)).where(db.Global_info.rend_ballon2 != None)
                rend = [row.rend_ballon2 for row in query]
                count_time = len(rend)
                #print(round(avg(rend),3), count_time, round(avg(rend),3)*count_time)
                # print(arange(0.1, 0.6, 0.1))
                if round(avg(rend),3)*count_time < 0.2:
                     print("Boost Sortie rend + ({}) rendement = {}°C".format(round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2), round(round(avg(rend),3)*count_time, 3)))
                     AjustTemp = round(AjustTemp+round(10-round(round(avg(rend),3)*(count_time*5),2)*2, 2))

            AjsutTemp = AjustTemp + 5

        if AjustTemp >= 100:
            AjustTemp = 99

    if force_variable == "auto":
        return round_of_8bit(AjustTemp)
    else:
        return force_variable

# def channelVoltage(channel, percent, disable=False):
#     PWMControl = PWMControl() #0:I2C  1: UART
#     #scr.GridFrequency(50)
#     #scr.SetMode(1)
#     #scr.GridFrequency(50)
#
#     if disable == False and percent > 0:
#         scr.ChannelEnable(channel)
#         scr.channelVoltage(channel, percent, max_charge=1500)
#
#     if percent == 0 and disable==True:
#         scr.channelVoltage(channel, percent, max_charge=1500)
#         scr.ChannelDisable(channel)
#

def SetResistance(sonde1, sonde2, temperature1, temperature2):

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
    query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).limit(1)
    Sonde2 = [[row.watt, row.moyenne_temperature] for row in query]

    if Sonde2[-1][0] == None:
        Sonde2[-1][0] = 0

    if Sonde2[-1][1] == None:
        query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.moyenne_temperature != None).limit(3)
        Sonde2_temp = [row.moyenne_temperature for row in query]
        Sonde2[-1][1] = avg(Sonde2_temp)

    if date.hour >= 21 or date.hour < 8:
        print("SAVE MODE >= 21 hours dans < 8 hours")

    #ENTRER
    if (temperature2 < 40 and (temperature1 >= 40)) or (temperature2 < 40 and Sonde2[-1][0] == 0):
        if date.hour >= 21 or date.hour < 8:
            Percent_R2 = AjustPercent(temperature2, 35, 10, "temp1")
        else:
            Temp_R2 = AjustPercent(temperature2, 40, 7, "temp1")
            if abs(temperature2-temperature1) >= 10 or Temp_R2 >= 30:
                Percent_R2 = AjustPercent(temperature2, 40, 7, "temp1")
            else:
                Percent_R2 = AjustPercent(temperature2, 35, 10, "temp1")

        if Percent_R2 != 0:
            Resistance2 = True
            db_save = db.Ballon1.create(date=date, resistance=Percent_R2, watt=round((Percent_R2/100*Resistance2_P)))
            db_save.save()
            print("Resistance 1 Entrer - Turn On {} - conso: {} - {}%".format(temperature2, round(Percent_R2/100*Resistance2_P), Percent_R2))
            #PWMControl.control(1, Percent_R2)

    # SORTIE
    # SOIR R2 OFF
    if date.hour >= 21 or date.hour < 8 and Resistance2 == False:
        Percent_R1 = AjustPercent(temperature1, 44, 5, "temp2") # jusqu'a 39

    # SOIR R2 ON
    elif  date.hour >= 21 or date.hour < 8 and Resistance2 == True:
        Percent_R1 = AjustPercent(temperature1, 44, 5, "temp2") # jusqu'a 39
        if Percent_R1 > 0:
            Percent_R1 = Percent_R1-5

    # journee R2 ON
    elif (date.hour < 21 or date.hour >= 8) and Resistance2 == True:
        Percent_R1 = AjustPercent(temperature1, 50, 5, "temp2") # jusqu'a 40

    # journee R2 OFF
    elif (date.hour < 21 or date.hour >= 8) and Resistance2 == False:
        Percent_R1 = AjustPercent(temperature1, 55, 7, "temp2")

    # mise en marche
    if temperature1 < 55:
        Resistance1 = True
        if Percent_R1 != 0:
            db_save = db.Ballon2.create(date=date, Sonde_haut=sonde1['haut']['temp'], Sonde_bas=sonde1['bas']['temp'], moyenne_temperature=temperature1, resistance=Percent_R1, watt=round((Percent_R1/100*Resistance1_P)))
            db_save.save()
            print("Resistance 2 Sortie - Turn On {} - conso: {} - {}%".format(temperature1, round(Percent_R1/100*Resistance1_P),  Percent_R1))
            #PWMControl.control(2, Percent_R1)

    return Percent_R2, Percent_R1

#security(msg="STOP FORCED")
sonde1 = GetSonde1()
sonde2 = GetSonde2()

# print("--------------- SORTIE ------------")
# print("Sonde 1 - Haut", sonde1['haut']['temp'], sonde1['haut']['resistance'])
# print("Avg Temp Sonde 1: {}".format(round(sonde1['moyenne'], 1)))
# print("Sonde 1 - Bas", sonde1['bas']['temp'], sonde1['bas']['resistance'])
# print("--------------- ENTRER -------------")
# print("Sonde 2 - Haut", sonde2['haut']['temp'], sonde2['haut']['resistance'])
# print("Avg temp Sonde 2: {}".format(round(sonde2['moyenne'], 1)))
# print("Sonde 2 - Bas", sonde2['bas']['temp'], sonde2['bas']['resistance'])
# print()

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

    # r = requests.get("http://192.168.1.14/getmeterdata").json()
    #
    # V = r["channels"][0]["V"]/1000
    # I = r["channels"][0]["I"]/1000
    # W = round(V*I)
    #
    # print("Watt Total:", W)

    R1, R2 = SetResistance(sonde1, sonde2, round(sonde1['moyenne'], 1), round(sonde2['moyenne'], 1))

    if R1 == 0:
        #PWMControl.control(1, R1)
        db_save = db.Ballon1.create(date=date, resistance=0, watt=0)
        db_save.save()

    if R2 == 0:
        #PWMControl.control(2, R2)
        db_save = db.Ballon2.create(date=date, resistance=0, watt=0)
        db_save.save()

        # total_watt_R1 = round((R1*1500)/100)
        # total_watt_R2 = round((R2*1500)/100)
        # watt1 = W-total_watt_R1
        # watt2 = watt1-total_watt_R2
        # print("dispath watt: ", watt2-400)
    #write_lcd(temp1=sonde1['moyenne'], temp2=sonde2['moyenne'])
print()
#conso = conso_global()
#print(conso)
exit(0)
