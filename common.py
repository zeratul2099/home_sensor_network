from datetime import datetime, timedelta
from math import exp

from sqlalchemy import create_engine, Table, MetaData, Column, String, Integer, Float, DateTime, desc
from sqlalchemy.exc import OperationalError, InternalError
import pytz

from settings import database, sensor_map


def get_sensor_name(sensor_id):
    if sensor_id:
        return sensor_map.get(sensor_id, 'DeviceID' + sensor_id)
    else:
        return None

def get_database():
    db = create_engine(database, pool_recycle=6*3600)
    metadata = MetaData(db)
    log = Table('sensor_log', metadata,
                Column('sensor_id', Integer, primary_key=True, nullable=True),
                Column('sensor_name', String(128)),
                Column('timestamp', DateTime, primary_key=True),
                Column('temperature', Float),
                Column('humidity', Float),
                )
    try:
        log.create()
    except (OperationalError, InternalError):
        # import traceback
        # traceback.print_exc()
        pass
    return log


def get_latest_values(tz_name=None, would_be=False):
    log = get_database()
    if tz_name is None:
        tz = pytz.utc
    else:
        tz = pytz.timezone(tz_name)
    latest_values = list()
    for sensor_id, sensor_name in sorted(sensor_map.items()):
        query = log.select().where(log.c.sensor_id == int(sensor_id)).order_by(desc(log.c.timestamp)).limit(1)
        row = query.execute().fetchall()[0]
        if row.timestamp < datetime.utcnow() - timedelta(hours=2):
            old_value = True
        else:
            old_value = False
        timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M')
        latest_values.append((sensor_id, sensor_name, timestamp, row.temperature, row.humidity, old_value))
    if would_be is True:
        would_be_values = list()
        # assume that the first "sensor" is outside
        for sensor_id, sensor_name, timestamp, temperature, humidity, old_value in latest_values[1:]:
            would_be_hum = transpose_humidity(latest_values[0][4], latest_values[0][5], temperature)
            would_be_values.append((str(int(sensor_id) + 100), sensor_name + '_x', timestamp,
                                    temperature, would_be_hum, old_value))
        latest_values += would_be_values
    return latest_values


def transpose_humidity(input_t, input_h, target_t):
    '''
    input_t: outsite temperature in C
    input_h: outsite humidity in %
    target_t: inside temperature in C

    '''
    Rv = 461.5
    t0 = input_t + 273.15
    p = 1024.0 # hPa
    ew0 = 6.112 * exp((17.62 * input_t) / (243.12 + input_t))
    fp = 1.0016 + 3.15 * 10**-6 * p - 0.074 * p**-1
    ew01 = fp * ew0 * 100
    e0 = ew01 * (input_h / 100)
    AH = e0 / (Rv * t0)
    # return AH
    t1 = target_t + 273.15
    e1 = AH * 461.5 * t1
    ew1 = 6.112 * exp((17.62 * target_t) / (243.12 + target_t))
    ew11 = fp * ew1 * 100
    target_h = 100 * e1 / ew11

    return target_h


    

