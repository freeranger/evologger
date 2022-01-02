"""
DarkSky input plugin - for getting the outside temperature
"""
# pylint: disable=C0103,W0703

from datetime import datetime
import random
import urllib.error
import forecastio
from config_helper import *
from Temperature import *

plugin_name = "DarkSky"
plugin_type = "input"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __config = get_config()

    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)

    __section = __config[plugin_name]
    __api_key = __section['apiKey']
    __latitude = __section['latitude']
    __longitude = __section['longitude']
    __zone = get_string_or_default(plugin_name, 'Outside', 'Outside')
    __logger.debug("Outside Zone: %s", __zone)

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True

def read():
    """
    Reads the outside temperature from DarkSky
    """    
    
    if __invalid_config:
        __logger.debug('Invalid config, aborting read')
        return []

    debug_message = f'Reading Temp for (lat: {__latitude}, long: {__longitude}) from {plugin_name}'
    if __simulation:
        debug_message += ' [SIMULATED]'
        __logger.debug(debug_message)

    if not __simulation:
        try:
            forecast = forecastio.load_forecast(__api_key, __latitude, __longitude)
        except urllib.error.HTTPError as e:
            __logger.exception(f'DarkSky API HTTPError - aborting write\n{e.read().decode()}')
        except Exception as e:
            __logger.exception(f'DarkSky API error - aborting read:\n{e}')
            return []

        temp = round(forecast.currently().temperature, 1)
    else:
        temp = round(random.uniform(12.0, 23.0), 1)

    if __simulation:
        __logger.info(f'[SIMULATED] {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}: {__zone} ({temp})')
    else:
        __logger.debug(f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}: {__zone} ({temp})')

    return [Temperature(__zone, temp)]

# if called directly then this is what will execute
if __name__ == "__main__":
    read()
