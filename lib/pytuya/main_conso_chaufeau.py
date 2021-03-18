import pytuya
import time
import pprint
#35466753483fda783614

d = pytuya.OutletDevice('35466753483fda783614', '192.168.1.212', 'ec83cabf1d40bc17')
d.set_version(3.3)

data = d.status()  # NOTE this does NOT require a valid key
print(data)

power = data['dps']['1']
kwh = int(data['dps']['17'])
MilAmp = int(data['dps']['18'])
Watt = int(data['dps']['19'])
Voltage = int(data['dps']['20'])

print("power {}".format(power))
print("kwh {}".format(kwh/1000))
print("Amp {}".format(MilAmp/1000))
print("Watt {}".format(Watt))
print("Voltage {}".format(Voltage/10))
print("VA {}".format(MilAmp*(Voltage/10)))

if power != True:
    d.set_status(True, 1)
# Toggle switch state
# '1': true, // turn on/off
# '2': 25, // temperature souhaiter
# '3': 20, // temperature piece
# '4': "hot", // hot,wet,cold,wind,auto
# '5': "low", //low,medium,high,auto vitesse ventilateur
# '9': false, // dry mode just for wet,cold mode
# '105': false, // silencieux mode on/off disable if mode strong
# '101': false, // sleep mode on/off
# '12': false, // heat mode just for hot mode on/off
# '13': true, // lumiere mode on/off
# '8': true, // mode eco on/off just for cold
# '107': true, // air movement haut/bas on/off
# '102': true // strong mode on/off disable if mode sleep

# settings = {
#  'power':  [1, data['dps']['1']],
#  'temp_souhaiter': [2, data['dps']['2']],
#  'temp_piece': [3, data['dps']['3']],
#  'mode': [4, data['dps']['4']],
#  'fan_speed': [5, data['dps']['5']],
#  'blow': [9, data['dps']['9']],
#  'silence': [105, data['dps']['105']],
#  'sleep': [101, data['dps']['101']],
#  'heat': [12, data['dps']['12']],
#  'lcd': [13, data['dps']['13']],
#  'eco': [8, data['dps']['8']],
#  'air_mode': [107, data['dps']['107']],
#  'turbo': [102, data['dps']['102']],
#  'Error': [108, data['dps']['108']],
#  'None': [[17, data['dps']['17']], [18, data['dps']['18']], [10, data['dps']['10']], [104, data['dps']['104']], [106, data['dps']['106']] ],
# }
#
# set_settings = {
#  'power': True,
#  'mode': "cold",
#  'lcd': True,
#  #'silence': True,
#  'fan_speed': "auto",
#  'lcd': True,
#  'blow': False,
#  'sleep': False,
#  #'temp_souhaiter': 26,
#  'air_mode': True,
#  'eco': True,
#  'turbo': False
# }
#
# #pprint.pprint(data['dps'])
# pprint.pprint(settings)
#
# for key, value in settings.items():
#     try:
#         if settings[key][1] != set_settings[key]:
#             print("set value {} {}".format(key, set_settings[key]))
#             data = d.set_status(set_settings[key], value[0])  # This requires a valid key
#             time.sleep(1)
#     except:
#         pass
