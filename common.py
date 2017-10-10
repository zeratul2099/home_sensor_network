from datetime import datetime, timedelta

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


def get_latest_values(tz_name=None):
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
    return latest_values
