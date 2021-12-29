"""
Console output plugin
"""
# pylint: disable=C0103,W0703

import sys
from config_helper import *

plugin_name = "Console"
plugin_type = "output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __hot_water = get_string_or_default('DEFAULT', 'HotWater', None)
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True


def write(timestamp, temperatures):
    """
    Writes the temperatures to the console
    """
    if __invalid_config:
        __logger.warning('Invalid config, aborting write')
        return

    debug_message = f'Writing to {plugin_name}'
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    try:
        text_temperatures = f'{timestamp}: '
        for t in temperatures:
            text_temperatures += f'{t.zone} ({t.actual}'

            if t.target is not None:
                text_temperatures += ' A'
                if t.zone == __hot_water and t.target == 0.0:
                    text_temperatures += ', OFF'
                else:
                    text_temperatures += f', {t.target} T'
            text_temperatures += ') '

        if  __simulation:
            __logger.info("[SIMULATED] %s", text_temperatures)
        else:
            __logger.debug(text_temperatures)
            print (text_temperatures)
    except Exception as e:
        __logger.exception(f'Error writing temperatures\n{e}')


# if called directly then this is what will execute
if __name__ == "__main__":
    write(sys.argv[1], sys.argv[2])
