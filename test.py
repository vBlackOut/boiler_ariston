import unittest
import pigpio

from main import Boiler_Ariston
from lib.pwmd import PWMControl
from lcd_start import LCD_DISPLAY
from rend import rendement


class TestBoiler(unittest.TestCase):

    boiler = Boiler_Ariston()

    def test_device_i2c(self):

        pi = pigpio.pi() # connect to local Pi

        # 0x27 Screen LCD for read instantly data
        # 0x2C potentiometrie for adjusting backligth screen
        # 0x48 for ADS1115 is device for check the potentometrie on NTC sonde

        check_list_device = ['0x27', '0x2c', '0x48']
        list_system_i2c = []

        for device in range(128):

          h = pi.i2c_open(1, device)
          try:
             pi.i2c_read_byte(h)
             list_system_i2c.append(hex(device))
          except: # exception if i2c_read_byte fails
             pass
          pi.i2c_close(h)

        pi.stop # disconnect from Pi

        self.assertEqual(check_list_device, list_system_i2c)


    def test_function_security(self):
        # return None if no error
        self.assertEqual(self.boiler.security(), None)

    def test_function_GetSonde_insidedb(self):

        # return dict
        # {"bas": {"temp": 34.6}, "haut": {"temp": 36.8}, "moyenne": 34.5}

        # check sonde1
        sonde1 = self.boiler.sonde2

        # check type return
        self.assertEqual(type(sonde1), dict)

        # check value if float or number and condition is operationnel
        self.assertTrue(isinstance(sonde1['bas']['temp'], float))
        self.assertTrue(sonde1['bas']['temp'] > 0 and sonde1['bas']['temp'] < 60)

        self.assertTrue(isinstance(sonde1['haut']['temp'], float))
        self.assertTrue(sonde1['haut']['temp'] > 0 and sonde1['haut']['temp'] < 60)

        # check sonde 2
        sonde2 = self.boiler.sonde2

        # check value if float or number and condition is operationnel
        self.assertTrue(isinstance(sonde2['bas']['temp'], float))
        self.assertTrue(sonde2['bas']['temp'] > 0 and sonde2['bas']['temp'] < 60)

        self.assertTrue(isinstance(sonde2['haut']['temp'], float))
        self.assertTrue(sonde2['haut']['temp'] > 0 and sonde2['haut']['temp'] < 60)


    def test_function_GetSonde_ousidedb(self):

        # this function call directly on GPIO the temperature
        lcd_function = LCD_DISPLAY("norun")

        sonde1 = lcd_function.GetSonde1()

        # check type return
        self.assertEqual(type(sonde1), dict)

        # check value if float or number and condition is operationnel
        self.assertTrue(isinstance(sonde1['bas']['temp'], float))
        self.assertTrue(sonde1['bas']['temp'] > 0 and sonde1['bas']['temp'] < 60)

        self.assertTrue(isinstance(sonde1['haut']['temp'], float))
        self.assertTrue(sonde1['haut']['temp'] > 0 and sonde1['haut']['temp'] < 60)

        sonde2 = lcd_function.GetSonde2(

        # check value if float or number and condition is operationnel
        self.assertTrue(isinstance(sonde2['bas']['temp'], float))
        self.assertTrue(sonde2['bas']['temp'] > 0 and sonde2['bas']['temp'] < 60)

        self.assertTrue(isinstance(sonde2['haut']['temp'], float))
        self.assertTrue(sonde2['haut']['temp'] > 0 and sonde2['haut']['temp'] < 60)


    def test_pwmcontrol(self):

        # get status on resistance electricity
        pwmcontrol = PWMControl()

        # check value of pwm1
        self.assertTrue(isinstance(pwmcontrol.angle1, float))
        self.assertTrue(pwmcontrol.angle1 >= 0 and pwmcontrol.angle1 <= 100)

        # check value of pwm2
        self.assertTrue(isinstance(pwmcontrol.angle2, float))
        self.assertTrue(pwmcontrol.angle2 >= 0 and pwmcontrol.angle2 <= 100)

    def test_setresistance(self):

        # define pwm percent for temperature check on NTC sonde

        sonde1 = self.boiler.sonde1
        sonde2 = self.boiler.sonde2

        # attrib : sonde1, sonde2, temperature_moyenne1, temperature_moyenne2
        R1, R2 = self.boiler.SetResistance(round(sonde1['moyenne'], 1), round(sonde2['moyenne'], 1), test=True)

        # get value of programme return R1, R2 algorithme of define power output on pwm (triac)
        self.assertTrue(isinstance(R1, float))
        self.assertTrue(isinstance(R2, float))

    def test_rendement(self):
        # test execution is on database
        rend = rendement(5)

        # rend is calculated temperature delta of 7 secondes later and now.
        self.assertTrue(isinstance(rend, float))

if __name__ == '__main__':
    unittest.main()
