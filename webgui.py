from datetime import datetime, timedelta
import json

import pytz
from flask import Flask, url_for, render_template, request, abort, jsonify
from sqlalchemy import desc, func, select as select_stm
from common import (
    get_database,
    get_sensor_name,
    get_latest_values,
    get_timespan_mean_values,
    check_notification,
    SETTINGS
)

app = Flask(__name__) # pylint: disable=invalid-name


@app.route('/')
@app.route('/<filter_sensor_id>')
def main(filter_sensor_id=None):
    page = request.args.get('page')
    if page is None:
        page = '0'
    pagesize = 50
    timezone = pytz.timezone(SETTINGS['timezone'])
    log = get_database()
    select = log.select()\
        .where(log.c.temperature.isnot(None))\
        .where(log.c.humidity.isnot(None))\
        .order_by(desc(log.c.timestamp))
    count = log.select()
    count = select_stm([func.count()]).select_from(log)
    if filter_sensor_id:
        select = select.where(log.c.sensor_id == int(filter_sensor_id))
        count = count.where(log.c.sensor_id == int(filter_sensor_id))
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
            sensor_id=row.sensor_id,
            sensor_name=row.sensor_name,
            timestamp=pytz.utc.localize(row.timestamp).\
                astimezone(timezone).strftime('%d.%m.%Y %H:%M:%S'),
            temperature=row.temperature,
            humidity=row.humidity,
        )
        result.append(entry)
    return render_template(
        'table.html',
        result=result,
        sensor_name=get_sensor_name(filter_sensor_id),
        page=page,
        maxpages=maxpages
    )


@app.route('/plots')
def plots():
    return render_template('plots.html', timezone=SETTINGS['timezone'])


@app.route('/gauges')
def gauges():
    return render_template(
        'gauges.html',
        sensor_map=SETTINGS['sensor_map'],
        timezone=SETTINGS['timezone']
    )


@app.route('/weather')
def weather():
    with open('weatherdump.json', 'r') as dumpfile:
        conditions = json.load(dumpfile)
    timezone = pytz.timezone(SETTINGS['timezone'])
    timestamp = datetime.utcfromtimestamp(conditions['currently']['time'])
    timestamp = pytz.utc.localize(timestamp).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
    return render_template('weather.html', conditions=conditions, timestamp=timestamp)


@app.route('/simple')
def simple():
    would_be = bool(request.args.get('wouldbe'))
    latest_values = get_latest_values(SETTINGS['timezone'], would_be=would_be)
    return render_template('simple.html', latest_values=latest_values)


@app.route('/mean')
def mean():
    end = datetime.utcnow()
    begin = end - timedelta(days=60)
    mean_values = get_timespan_mean_values(begin, end)
    return render_template('mean.html', mean_values=mean_values)


# api
@app.route('/api/history')
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
        timezone = pytz.utc
    else:
        timezone = pytz.timezone(tz_name)
    now = datetime.utcnow()
    history = list()
    for sensor_id, sensor_name in sorted(SETTINGS['sensor_map'].items()):
        history.append((sensor_id, sensor_name, list()))
        query = log.select().where(log.c.sensor_id == int(sensor_id))\
            .where(log.c.timestamp > now - timedelta(days=1))
        for row in query.execute().fetchall():
            timestamp = pytz.utc.localize(row.timestamp)\
                .astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
            if vtype == 't':
                value = row.temperature
            elif vtype == 'h':
                value = row.humidity
            history[-1][2].append([timestamp, value])
    return jsonify(*history)


@app.route('/api/latest')
def api_latest():
    latest_values = get_latest_values(request.args.get('tz'))
    return jsonify(*latest_values)

@app.route('/api/send')
def api_send():
    try:
        sensor_id = request.args.get('id')
        temp = float(request.args.get('t'))
        hum = float(request.args.get('h'))
    except ValueError:
        raise Exception('invalid values in %s' % request.args)

    sensor_name = get_sensor_name(sensor_id)
    log = get_database()
    now = datetime.utcnow()
    insert = log.insert() # pylint: disable=no-value-for-parameter
    insert.execute(
        sensor_id=sensor_id,
        sensor_name=sensor_name,
        timestamp=now,
        temperature=temp,
        humidity=hum
    )
    check_notification(int(sensor_id), 't', temp, now)
    check_notification(int(sensor_id), 'h', hum, now)
    return jsonify('OK')

@app.route('/favicon.ico')
def favicon():
    abort(404)


with app.test_request_context():
    url_for('static', filename='styles.css')


if __name__ == '__main__':
    app.run()
