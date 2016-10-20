#!/usr/bin/python
from datetime import datetime
import serial

from common import get_database, get_sensor_name
from settings import device


def main():
    print('Listening to %s...' % device)
    log = get_database()
    while(True):
        ser = serial.Serial(device, 9600)
        line = ser.readline().decode('utf8').strip()
        print('Received input: ' + line)
        keys = line.split(':')[0::2]
        values = line.split(':')[1::2]
        value_dict = dict(zip(keys, values))
        try:
            assert('ID' in keys and 'TS' in keys)
        except AssertionError:
            print('invalid input')
            continue
        sensor = get_sensor_name(value_dict['ID'])
        now = datetime.utcnow()
        print('%s: Sensor: %s, Temperature: %s, Humidity: %s' %
            (now.strftime('%Y-%m-%d %H:%M:%S'), sensor, value_dict['TC'], value_dict['RH']))
        try:
            temperature = float(value_dict['TC'])
        except ValueError:
            temperature = None
        try:
            humidity = float(value_dict['RH'].strip('%'))
        except ValueError:
            humidity = None
        insert = log.insert()
        insert.execute(sensor_id=int(value_dict['ID']), sensor_name=sensor,
                       timestamp=now, temperature=temperature,
                       humidity=humidity
                      )


if __name__ == '__main__':
    main()
