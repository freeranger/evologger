from Temperature import *
import forecastio
from config_helper import *
from datetime import datetime
import random

plugin_name = "darksky.net"
plugin_type = "input"

forecast_logger = logging.getLogger('darksky-plugin:')

invalidConfig = False

try:
    config = configparser.ConfigParser(allow_no_value=True)
    config.read('config.ini')

    forecast_debug_enabled = is_debugging_enabled('DarkSky')
    forecast_read_enabled = not get_boolean_or_default('DarkSky', 'Simulation', False)

    forecast_api_key = config.get("DarkSky", "apiKey")
    forecast_latitude = config.getfloat("DarkSky", "latitude")
    forecast_longitude = config.getfloat("DarkSky", "longitude")
    if config.has_option("DarkSky", "Outside"):
        forecast_zone = config.get("DarkSky", "Outside")
    else:
        forecast_zone = "Outside"

except Exception as e:
    forecast_logger.error("Error reading config:\n%s", e)
    invalidConfig = True

def read():

    if invalidConfig:
        if forecast_debug_enabled:
            forecast_logger.debug('Invalid config, aborting read')
            return []

    debug_message = 'Reading Temp for (lat: %s, long: %s) from %s' % (forecast_latitude, forecast_longitude, plugin_name)
    if not forecast_read_enabled:
        debug_message += ' [SIMULATED]'
        forecast_logger.debug(debug_message)

    if forecast_read_enabled:
        try:
            forecast = forecastio.load_forecast(forecast_api_key, forecast_latitude, forecast_longitude)
        except Exception as e:
            forecast_logger.error("DarkSky API error - aborting read:\n%s", e)
            return []

        temp = round(forecast.currently().temperature, 1)
    else:
        temp = round(random.uniform(12.0, 23.0), 1)

    if forecast_debug_enabled:
        forecast_logger.debug('%s: %s (%s)', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), forecast_zone, temp)

    return [Temperature(forecast_zone, temp)]

# if called directly then this is what will execute
if __name__ == "__main__":
    read()

