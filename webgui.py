from datetime import datetime, timedelta

import pytz
from flask import Flask, url_for, render_template, request, abort, jsonify
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
    return render_template('plots.html', timezone=timezone)


@app.route('/gauges')
def gauges():
    return render_template('gauges.html', sensor_map=sensor_map, timezone=timezone)


# api
@app.route('/history')
def api_history():
    log = get_database()
    vtype = request.args.get('type')
    if not vtype or vtype.lower() in ['t', 'temp', 'temperature']:
        vtype = 't'
    elif vtype.lower() in ['h', 'hum', 'humidity']:
        vtype = 'h'
    else:
        raise ValueError('wrong type')

    tz_name = request.args.get('tz')
    if tz_name is None:
        tz = pytz.utc
    else:
        tz = pytz.timezone(tz_name)
    now = datetime.utcnow()
    temperatures = dict()
    humidities = dict()
    history = list()
    for sensor_id, sensor_name in sorted(sensor_map.items()):
        history.append((sensor_id, sensor_name, list()))
        query = log.select().where(log.c.sensor_id == int(sensor_id)).where(log.c.timestamp > now - timedelta(days=1))
        for row in query.execute().fetchall():
            timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            if vtype == 't':
                value = row.temperature
            elif vtype == 'h':
                value = row.humidity
            history[-1][2].append([timestamp, value])
    return jsonify(*history)

    


@app.route('/latest')
def api_latest():
    log = get_database()
    tz_name = request.args.get('tz')
    if tz_name is None:
        tz = pytz.utc
    else:
        tz = pytz.timezone(tz_name)
    latest_values = list()
    for sensor_id, sensor_name in sorted(sensor_map.items()):
        query = log.select().where(log.c.sensor_id == int(sensor_id)).order_by(desc(log.c.timestamp)).limit(1)
        row = query.execute().fetchall()[0]
        timestamp = pytz.utc.localize(row.timestamp).astimezone(tz).strftime('%Y-%m-%d %H:%M')
        latest_values.append((sensor_id, sensor_name, timestamp, row.temperature, row.humidity))
    return jsonify(*latest_values)

@app.route('/favicon.ico')
def favicon():
    abort(404)    


with app.test_request_context():
    url_for('static', filename='styles.css')

if __name__ == '__main__':
    app.run()

