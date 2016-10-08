from sqlalchemy import create_engine, Table, MetaData, Column, String, Integer, Float, DateTime
from sqlalchemy.exc import OperationalError

from settings import database

def get_database():
    db = create_engine(database)
    metadata = MetaData(db)
    log = Table('sensor_log', metadata,
                Column('sensor_id', Integer, primary_key=True),
                Column('sensor_name', String(128)),
                Column('timestamp', DateTime, primary_key=True),
                Column('temperature', Float),
                Column('humidity', Float),
                )
    try:
        log.create()
    except OperationalError:
        # import traceback
        # traceback.print_exc()
        pass
    return log
