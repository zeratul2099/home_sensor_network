#!/usr/bin/python
import socket
from datetime import datetime
import serial
import time

import requests

from common import get_database, get_sensor_name
from settings import device, pa_app_token, pa_user_key, notification_constraints

NOTIFIED = set()


def send_message_retry(message, retries=3):

    for retry in range(retries):
        try:
            r = requests.post(
                'https://api.pushover.net/1/messages.json',
                data={'token': pa_app_token, 'user': pa_user_key, 'message': message},
            )
            print(r.text)
            break
        except (socket.gaierror, requests.exceptions.ConnectionError):
            print('retry')
            time.sleep(1)
            continue


def check_notification(sensor, vtype, value, ts):
    global NOTIFIED
    for idx, (csensor, ctype, cvalue, cmp) in enumerate(notification_constraints):
        if sensor == csensor and ctype == vtype:
            sensor_name = get_sensor_name(str(sensor))
            if idx not in NOTIFIED:
                if (cmp == '+' and value > cvalue) or (cmp == '-' and value < cvalue):
                    # notify
                    cmp_word = 'over' if cmp == '+' else 'below'
                    msg = '%s: %s is %s limit of %s (%s)' % (sensor_name, vtype, cmp_word, cvalue, ts)
                    print(msg)
                    send_message_retry(msg)
                    NOTIFIED.add(idx)
            elif (cmp == '+' and value < cvalue) or (cmp == '-' and value > cvalue):
                cmp_word = 'below' if cmp == '+' else 'over'
                msg = '%s all clear: %s is %s limit of %s again (%s)' % (sensor_name, vtype, cmp_word, cvalue, ts)
                print(msg)
                send_message_retry(msg)
                NOTIFIED.remove(idx)


def main():
    print('Listening to %s...' % device)
    log = get_database()
    while True:
        ser = serial.Serial(device, 9600)
        line = ser.readline().decode('utf8').strip()
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
        check_notification(sensor_id, 't', temperature, now)
        check_notification(sensor_id, 'h', humidity, now)


if __name__ == '__main__':
    main()
