from datetime import datetime

import pytz
import requests

from common import get_database
from settings import darksky_api_key, lat_lon


def main():
    url = 'https://api.darksky.net/forecast/%s/%s,%s?exclude=minutely,hourly,daily,alerts,flags&units=si'
    url = url % (darksky_api_key, lat_lon[0], lat_lon[1])
    response = requests.get(url)
    result = response.json()
    tz = pytz.timezone(result['timezone'])
    current_conditions = result['currently']
    timestamp = tz.localize(datetime.fromtimestamp(current_conditions['time'])).astimezone(pytz.utc)
    temperature = current_conditions['temperature']
    humidity = current_conditions['humidity'] * 100.0
    print(timestamp, temperature, humidity)

    log = get_database()
    insert = log.insert()
    insert.execute(sensor_id=0, sensor_name='Outside',
                   timestamp=timestamp, temperature =temperature,
                   humidity=humidity)


if __name__ == '__main__':
    main()
