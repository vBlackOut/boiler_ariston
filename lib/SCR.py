#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
import time

import os
import sys
# libdir = os.path.dirname(os.path.realpath(__file__))
# if os.path.exists(libdir):
#     sys.path.append(libdir)
from lib.config import config

CH_EN = [0x57,0x68,0x02,0x00,0x00,0x00]

class SCR:
    def __init__(self,Baudrate = 115200, dev = "/dev/tty0", data_mode = 1, address=0x47):
        self.address = address
        self.data_mode = data_mode #1 :uart   0: i2c
        self.Baudrate = Baudrate
        self.dev = dev
        self.com = config(Baudrate , dev, data_mode, address)
        self.angle1 = 0
        self.angle2 = 0
        self.read_file()

    def SendCommand(self, Data):
        if(self.data_mode == 1):
            #Data[6] = '\0'
            #self.com.UART_SendString(Data);
            self.com.UART_SendnByte(Data,6)
        if(self.data_mode == 0):# 0: i2c
            #print("data send: {}".format(Data[2], (Data[3]) | (Data[4]<<8)))
            self.com.I2C_SendWord(Data[2], (Data[3]) | (Data[4]<<8))
        time.sleep(0.2)

    def SET_Check_Digit(self, Data):
        #print("check digital : {}".format(((((Data[0]^Data[1])^Data[2])^Data[3])^Data[4])))
        return  ((((Data[0]^Data[1])^Data[2])^Data[3])^Data[4])

    def SetMode(self, Mode):
        ch=[0x57,0x68,0x01,0x00,0x00,0x00]
        ch[4] = Mode&0x01
        ch[5] = self.SET_Check_Digit(ch)
        print("mode: {}".format(ch))
        self.SendCommand(ch);

    def channelVoltage(self, channel, percent, max_charge=2200):

        percent_usable = (max_charge * 100) / 2200
        percent_usable = round((180 * percent_usable) /100)

        percent = round((percent*percent_usable)/100)

        percent_channel1 = self.angle1
        percent_channel2 = self.angle2

        #print(channel, percent, percent_channel1, percent_channel2)

        if channel == 1:
            if percent != percent_channel1:
                if percent > percent_channel1:
                    print("ch1 {} -> {} (+{})".format(percent_channel1, percent, abs(percent_channel1-(percent))))
                    for i in range(0, abs(percent_channel1-(percent))+1):
                        time.sleep(0.2)
                        angle = self.angle1+i
                        self.VoltageRegulation(channel, angle)
                        if angle == percent or angle >= percent or angle >= 180:
                            break

                elif percent < percent_channel1:
                    print("ch1 {} -> {} (-{})".format(percent_channel1, percent, percent_channel1-(percent)))
                    for i in range(0, percent_channel1-(percent-1)):
                        time.sleep(0.2)
                        angle = self.angle1-i
                        self.VoltageRegulation(channel, angle)
                        if angle == percent or angle <= 0:
                            break
                self.angle1 = percent

        if channel == 2:
            if percent != percent_channel2:
                if percent > percent_channel2:
                    print("ch2 {} -> {} (+{})".format(percent_channel2, percent, abs(percent_channel2-(percent))))
                    # for i in range(percent_channel2, percent+1):
                    for i in range(0, abs(percent_channel2-(percent))+1):
                        time.sleep(0.2)
                        angle = self.angle2+i
                        print(i, angle)
                        self.VoltageRegulation(channel, angle)
                        if angle == percent or angle >= 180:
                            break

                elif percent < percent_channel2:
                    print("ch2 {} -> {} (-{})".format(percent_channel2, percent, percent_channel2-(percent)))
                    for i in range(0, percent_channel2-(percent-1)):
                        time.sleep(0.2)
                        angle = self.angle2-i
                        print(i, angle)
                        self.VoltageRegulation(channel, angle)
                        if angle == percent or angle <= 0:
                            break
                self.angle2 = percent

    def read_file(self):
        f = open("/home/pi/Python/ADS/logs.txt", "r")
        for i in f.readlines():
            lines = i.split(" ")

        self.angle1 = int(lines[1])
        self.angle2 = int(lines[0])
        #print("debug angle: ", self.angle2, self.angle1)

    def write_file(self, angle1="", angle2=""):

        f = open("/home/pi/Python/ADS/logs.txt", "w")
        if angle2 != "":
            f.write("{} {}".format(angle2, self.angle1))
        elif angle1 != "":
            f.write("{} {}".format(self.angle2, angle1))
        f.close()

    def ChannelEnable(self, Channel):
        if(Channel == 1):
            CH_EN[4] = 0x01|CH_EN[4]
            CH_EN[5] = self.SET_Check_Digit(CH_EN)
            #print("enable1 : {}".format(CH_EN))
            self.SendCommand(CH_EN)

        elif(Channel == 2):
            CH_EN[4] = 0x02|CH_EN[4]
            CH_EN[5] = self.SET_Check_Digit(CH_EN)
            #print("enable2 : {}".format(CH_EN))
            self.SendCommand(CH_EN)

    def ChannelDisable(self,Channel):
        if(Channel == 1):
            CH_EN[4] = 0xfe & CH_EN[4]
            CH_EN[5] = self.SET_Check_Digit(CH_EN)
            self.SendCommand(CH_EN)

        elif(Channel == 2):
            CH_EN[4] = 0xfd & CH_EN[4]
            CH_EN[5] = self.SET_Check_Digit(CH_EN)
            self.SendCommand(CH_EN)

    def VoltageRegulation(self, Channel, Angle):
        time.sleep(0.2)
        Angle1 = [0x57,0x68,0x03,0x00,0x00,0x00]
        Angle2 = [0x57,0x68,0x04,0x00,0x00,0x00]

        if (Channel == 1):
            Angle1[4] = Angle
            Angle1[5] = self.SET_Check_Digit(Angle1)
            self.SendCommand(Angle1)
            #print("out 1:", Angle)
            self.write_file(angle1=Angle)

        if (Channel == 2):
            Angle2[4] = Angle
            Angle2[5] = self.SET_Check_Digit(Angle2)
            self.SendCommand(Angle2)
            #print("out 2:", Angle)
            self.write_file(angle2=Angle)

    def GridFrequency(self, Hz):
        Frequency = [0x57, 0x68, 0x05, 0x00, 0x32, 0x00]
        # if (Hz == 50 or Hz == 60):
        Frequency[4] = Hz
        Frequency[5] = self.SET_Check_Digit(Frequency)
        self.SendCommand(Frequency);

    def Reset(self, Delay):
        ch=[0x57,0x68,0x06,0x00,0x00,0x00]
        ch[4] = Delay & 0xff
        ch[3] = Delay >> 8
        ch[5] = self.SET_Check_Digit(ch)
        self.SendCommand(ch)
        self.write_file(angle1=0)
        self.write_file(angle2=0)
