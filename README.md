# home_sensor_network

python component for a Raspberry Pi/Arduino-driven wireless sensor network for temperature and humidity which is described here:

https://computers.tutsplus.com/tutorials/building-a-wireless-sensor-network-in-your-home--cms-19745

As opposed to the original code, this one stores the sensor values in a local database.

Optionally you can collect outside temperature and humidity for you location via the Darksky-API (https://darksky.net). You need
to get an Darksky-API-Key and enter it with your geolocation in the settings and then let weather_condition.py run per crontab (e.g. \*/15)

Dependencies:
 - python3
 - sqlalchemy
 - flask
 - pytz
 - requests

External libraries:
 - jquery: https://jquery.org/license
 - jqplot: https://jqplot.com/info.php




Upcoming features:
 - navigation, layout
