#!/usr/bin/python
import socket
from datetime import datetime
import serial
import time

import requests

from common import get_database, get_sensor_name, check_notification
from settings import device


def main():
    print('Listening to %s...' % device)
    log = get_database()
    while True:
        ser = serial.Serial(device, 9600)
        try:
            line = ser.readline().decode('utf8').strip()
        except UnicodeDecodeError:
            print('UnicodeDecodeError')
            continue
        print('Received input: ' + line)
        keys = line.split(':')[0::2]
        values = line.split(':')[1::2]
        value_dict = dict(zip(keys, values))
        try:
            assert 'ID' in keys and 'TS' in keys
        except AssertionError:
            print('invalid input')
            continue
        sensor = get_sensor_name(value_dict['ID'])
        now = datetime.utcnow()
        print(
            '%s: Sensor: %s, Temperature: %s, Humidity: %s'
            % (now.strftime('%Y-%m-%d %H:%M:%S'), sensor, value_dict.get('TC', 'NaN'), value_dict.get('RH', 'NaN'))
        )
        try:
            temperature = float(value_dict['TC'])
        except (ValueError, KeyError):
            temperature = None
        try:
            humidity = float(value_dict['RH'].strip('%'))
        except (ValueError, KeyError):
            humidity = None
        insert = log.insert()
        sensor_id = int(value_dict['ID'])
        insert.execute(
            sensor_id=sensor_id, sensor_name=sensor, timestamp=now, temperature=temperature, humidity=humidity
        )
        if temperature is not None:
            check_notification(sensor_id, 't', temperature, now)
        if humidity is not None:
            check_notification(sensor_id, 'h', humidity, now)


if __name__ == '__main__':
    main()
