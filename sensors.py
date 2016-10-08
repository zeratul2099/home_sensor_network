#!/usr/bin/python
from datetime import datetime
import serial

from common import get_database
from settings import device, database, sensor_map




def main():
    log = get_database()
    while(True):
        ser = serial.Serial(device, 9600)
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
        now = datetime.utcnow()
        print('%s: Sensor: %s, Temperature: %s, Humidity: %s' %
            (now.strftime('%Y-%m-%d %H:%M:%S'), sensor, value_dict['TC'], value_dict['RH']))
        insert = log.insert()
        insert.execute(sensor_id=int(value_dict['ID']), sensor_name=sensor,
                       timestamp=now, temperature=float(value_dict['TC']),
                       humidity=float(value_dict['RH'].strip('%'))
                      )

if __name__ == '__main__':
    main()
