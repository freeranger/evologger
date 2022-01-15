"""
EMON CMS output plugin
"""

import sys
import time
import requests
from config_helper import *

plugin_name = "Emoncms"
plugin_type = "output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __config = get_config()
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)

    __api_key = __config.get(plugin_name, "apiKey")
    __node = __config.get(plugin_name, "node")

    __post_url=f'http://emoncms.org/input/post?apikey={__api_key}&node={__node}'

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True


def write(timestamp, temperatures):
    """
    Writes the temperatures to emoncms.org
    """

    if __invalid_config:
        __logger.debug('Invalid config, aborting write')
        return

    debug_message = 'Writing to ' + plugin_name
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    text_temperatures = f'{timestamp}: '
    url = f'{__post_url}&time={time.mktime(timestamp.timetuple())}&json={{'

    for temperature in temperatures:
        url = f'{url}{temperature.zone} Actual: {str(temperature.actual)},'
        text_temperatures += f'{temperature.zone} ({temperature.actual} A'
        if temperature.target is not None:
            url += f'{temperature.zone} Target: {str(temperature.target)},'
            text_temperatures += f', {temperature.target} T) '

    url += '}'
    url = url.replace(",}", "}")
    url = url.replace(" ", "")
    text_temperatures += ') '

    try:
        if __simulation:
            __logger.info("[SIMULATED] %s", text_temperatures)
        else:
            __logger.debug(text_temperatures)
            __logger.debug('URL: %s',url)
            with requests.get(url) as response:
                __logger.debug(f'Emon API response: {response.status_code} {response.reason} {response.content}') # pylint disable=W1201
                response.raise_for_status()
    except requests.HTTPError as e:
        __logger.exception(f'Emon API HTTPError {response.status_code} {response.reason} - aborting write\n{e}')
    except Exception as e:
        __logger.exception(f'Emon API error - aborting write\n{e}')


# if called directly then this is what will execute
if __name__ == "__main__":
    write(sys.argv[1], sys.argv[2])
