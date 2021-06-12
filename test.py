import unittest
from main import Boiler_Ariston
from lib.pwmd import PWMControl


class TestBoiler(unittest.TestCase):

    boiler = Boiler_Ariston()

    def test_function_security(self):
        # return None if no error
        self.assertEqual(self.boiler.security(), None)

    def test_function_GetSonde_insidedb(self):

        # return dict
        # {"bas": {"temp": 34.6}, "haut": {"temp": 36.8}, "moyenne": 34.5}

        # check sonde1
        sonde1 = self.boiler.GetSonde1()

        # check type return
        self.assertEqual(type(sonde1), dict)

        # check value if float or number and condition is operationnel
        self.assertTrue(isinstance(sonde1['bas']['temp'], float))
        self.assertTrue(sonde1['bas']['temp'] > 0 and sonde1['bas']['temp'] < 60)

        self.assertTrue(isinstance(sonde1['haut']['temp'], float))
        self.assertTrue(sonde1['haut']['temp'] > 0 and sonde1['haut']['temp'] < 60)

        # check sonde 2
        sonde2 = self.boiler.GetSonde2()

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


if __name__ == '__main__':
    unittest.main()
