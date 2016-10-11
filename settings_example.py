# serial device, ttyS0 for Raspberry Pi 3, ttyAMA0 for older models
device = '/dev/ttyS0'

# database for logging
database = 'sqlite:///sensor_log.db'

# sensor name mapping
sensor_map = {
    '1': 'Sensor 1',
    '2': 'Sensor 2',
    '3': 'Sensor 3',
}

# timezone shown in webgui
timezone = 'CET'

# darksky api key for outside temperature
darksky_api_key = None

# your location
lat_lon (50.0, 10.0)
