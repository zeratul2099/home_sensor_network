from datetime import datetime, timedelta
from math import exp

import numpy
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
    db = create_engine(database, pool_recycle=6 * 3600)
    metadata = MetaData(db)
    log = Table(
        'sensor_log',
        metadata,
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
        query = log.select().where(log.c.sensor_id == int(sensor_id)).where(log.c.temperature != None).where(log.c.humidity != None).order_by(desc(log.c.timestamp)).limit(1)
        row = query.execute().fetchall()[0]
        if row.timestamp < datetime.utcnow() - timedelta(hours=2):
            old_value = True
        else:
            old_value = False
        timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M')
        # assume that the first "sensor" is outside
        if sensor_id != '0' and would_be is True:
            would_be_hum = transpose_humidity(latest_values[0][3], latest_values[0][4], row.temperature)
        else:
            would_be_hum = None
        latest_values.append(
            (sensor_id, sensor_name, timestamp, row.temperature, row.humidity, would_be_hum, old_value)
        )
    return latest_values


def get_day_mean_values(sensor_id, day, log=None):
    if log is None:
        log = get_database()
    begin = datetime(day.year, day.month, day.day, 0, 0)
    end = datetime(day.year, day.month, day.day, 23, 59)
    query = (
        log.select()
        .where(log.c.sensor_id == int(sensor_id))
        .where(log.c.timestamp >= begin)
        .where(log.c.timestamp <= end)
    )
    ts = list()
    hs = list()
    for row in query.execute().fetchall():
        ts.append(row.temperature)
        hs.append(row.humidity)
    ts = numpy.array(ts)
    hs = numpy.array(hs)
    t_mean = numpy.mean(ts)
    h_mean = numpy.mean(hs)
    return begin, t_mean, h_mean


def get_timespan_mean_values(begin, end):
    result = dict()
    log = get_database()
    for sensor_id, sensor_name in sensor_map.items():
        current = begin
        while current <= end:
            day, t, h = get_day_mean_values(sensor_id, current, log=log)
            result.setdefault(sensor_name, list()).append((day, t, h))
            current += timedelta(days=1)
    return result


def transpose_humidity(input_t, input_h, target_t):
    '''
    input_t: outsite temperature in C
    input_h: outsite humidity in %
    target_t: inside temperature in C

    '''
    Rv = 461.5
    t0 = input_t + 273.15
    p = 1024.0  # hPa
    ew0 = 6.112 * exp((17.62 * input_t) / (243.12 + input_t))
    fp = 1.0016 + 3.15 * 10 ** -6 * p - 0.074 * p ** -1
    ew01 = fp * ew0 * 100
    e0 = ew01 * (input_h / 100)
    AH = e0 / (Rv * t0)
    t1 = target_t + 273.15

    e1 = AH * 461.5 * t1
    ew1 = 6.112 * exp((17.62 * target_t) / (243.12 + target_t))
    ew11 = fp * ew1 * 100
    target_h = 100 * e1 / ew11

    return target_h
