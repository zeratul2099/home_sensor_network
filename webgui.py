import pytz
from flask import Flask, url_for, render_template, request
from sqlalchemy import desc, func
from common import get_database
app = Flask(__name__)


@app.route('/')
@app.route('/<filter_sensor_id>')
def main(sensor_id=None):
    page = request.args.get('page')
    if page is None:
        page = '0'
    pagesize = 50
    cet = pytz.timezone('CET')
    log = get_database()
    select = log.select().order_by(desc(log.c.timestamp))
    count = log.select()
    if sensor_id:
        select = select.where(log.c.sensor_id==int(filter_sensor_id))
        count = count.where(log.c.sensor_id==int(filter_sensor_id))
    if page != 'all':
        count = count.count().execute().fetchone()[0]
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
            timestamp = pytz.utc.localize(row.timestamp).astimezone(cet).strftime('%d.%m.%Y %H:%M:%S'),
            temperature = row.temperature,
            humidity = row.humidity,
        )
        result.append(entry)
    return render_template('webgui.html', result=result, hostname=filter_sensor_id, page=page, maxpages=maxpages)


with app.test_request_context():
    url_for('static', filename='styles.css')

if __name__ == '__main__':
    app.run()

