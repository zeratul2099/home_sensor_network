#!/usr/bin/python
from datetime import datetime
import serial


# sensor name mapping
sensor_map = {
    '1': 'Sensor 1',
    '2': 'Sensor 2',
    '3': 'Sensor 3',
}

DEVICE = '/dev/ttyS0'
 
def main():
    while(True):
        ser = serial.Serial(DEVICE, 9600)
        line = ser.readline().strip()
        print('Received input: ' + line)
        splitList=line.split(":")
        keys = line.split(':')[0::2]
        values = line.split(':')[1::2]
        value_dict = dict(zip(keys, values))
        try:
            assert('ID' in keys and 'TS' in keys)
        except AssertionError:
            print('invalid input')
            continue
        sensor = sensor_map.get(value_dict['ID'], 'DeviceID' + value_dict['ID'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('%s: Sensor: %s, Temperature: %s, Humidity: %s' % (now, sensor, value_dict['TC'], value_dict['RH']))

if __name__ == '__main__':
    main()
