#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import numpy as np
import time
import os, sys
from daemonize import Daemonize
sys.path.append("..")
from database import db
from lib.daemon import *


class PWMControl():

    def __init__(self):

        angle1 = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.resistance != None).limit(1)
        angle1 = [row.resistance for row in angle1]

        angle2 = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.resistance != None).limit(1)
        angle2 = [row.resistance for row in angle2]

        self.angle1 = angle1[0]
        self.angle2 = angle2[0]
