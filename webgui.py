from datetime import datetime, timedelta

import pytz
from flask import Flask, url_for, render_template, request
from sqlalchemy import desc, func, select as select_stm
from common import get_database, get_sensor_name
from settings import sensor_map, timezone
app = Flask(__name__)


@app.route('/')
@app.route('/<filter_sensor_id>')
def main(filter_sensor_id=None):
    page = request.args.get('page')
    if page is None:
        page = '0'
    pagesize = 50
    tz = pytz.timezone(timezone)
    log = get_database()
    select = log.select().order_by(desc(log.c.timestamp))
    count = log.select()
    count = select_stm([func.count()]).select_from(log)
    if filter_sensor_id:
        select = select.where(log.c.sensor_id==int(filter_sensor_id))
        count = count.where(log.c.sensor_id==int(filter_sensor_id))
    if page != 'all':
        count = count.execute().fetchone()[0]
        maxpages = count // pagesize
        select = select.limit(pagesize)
        select = select.offset(int(page) * pagesize)
    else:
        maxpages = None
    rows = select.execute()
    result = list()
    for row in rows.fetchall():
        entry = dict(
            sensor_id = row.sensor_id,
            sensor_name = row.sensor_name,
            timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%d.%m.%Y %H:%M:%S'),
            temperature = row.temperature,
            humidity = row.humidity,
        )
        result.append(entry)
    return render_template('table.html', result=result, sensor_name=get_sensor_name(filter_sensor_id),
                           page=page, maxpages=maxpages)



@app.route('/plots')
def plots():
    log = get_database()
    tz = pytz.timezone(timezone)
    now = datetime.utcnow()
    temperatures = dict()
    humidities = dict()
    for sensor_id in sensor_map:
        query = log.select().where(log.c.sensor_id == int(sensor_id)).where(log.c.timestamp > now - timedelta(days=1))
        for row in query.execute().fetchall():
            timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M')
            temperatures.setdefault(sensor_id, list()).append([timestamp, row.temperature])
            humidities.setdefault(sensor_id, list()).append([timestamp, row.humidity])
    return render_template('plots.html', temperatures=sorted(temperatures.items()),
                           humidities=sorted(humidities.items()), sensor_map=sensor_map)


@app.route('/gauges')
def gauges():
    log = get_database()
    tz = pytz.timezone(timezone)
    now = datetime.utcnow()
    temperatures = list()
    humidities = list()
    for sensor_id, _ in sorted(sensor_map.items()):
        query = log.select().where(log.c.sensor_id == int(sensor_id)).order_by(desc(log.c.timestamp)).limit(1)
        row = query.execute().fetchall()[0]
        timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M')
        temperatures.append((sensor_id, timestamp, [row.temperature]))
        humidities.append((sensor_id, timestamp, [row.humidity]))

    return render_template('gauges.html', temperatures=temperatures,
                           humidities=humidities, sensor_map=sensor_map)



with app.test_request_context():
    url_for('static', filename='styles.css')

if __name__ == '__main__':
    app.run()

