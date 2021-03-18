import pytuya
import time
import pprint
#35466753483fda783614

d = pytuya.OutletDevice('', '192.168.1.212', '')
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
