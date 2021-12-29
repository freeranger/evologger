"""
CSV file output plugin
"""
# pylint: disable=C0103,R1732,W0406,W0703

import csv
import os.path
import sys
from config_helper import *

plugin_name = "Csv"
plugin_type = "output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __config = get_config()
    __filename = __config.get(plugin_name, "filename")
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True

def write(timestamp, temperatures):
    """
    Writes the temperatures to the configured file
    """    
    if __invalid_config:
        __logger.warning('Invalid config, aborting write')
        return

    debug_message = f'Writing to {plugin_name} ({__filename})'
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    csv_file = None
    writer = None

    csv_write_headers = not __simulation and not os.path.isfile(__filename)

    if not __simulation:
        try:
            csv_file = open(__filename, 'a', encoding='UTF-8')
        except Exception as e:
            __logger.exception(f'Error opening {__filename} for writing - aborting write\n{e}')
            return

        writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    if not __simulation and csv_write_headers:

        __logger.debug(f'Creating {__filename}')

        fieldnames = ['Time']
        for t in temperatures:
            if t.target is not None:
                fieldnames.append(t.zone + ' [A]')
                fieldnames.append(t.zone + ' [T]')
            else:
                fieldnames.append(t.zone)

        writer.writerow(fieldnames)

    text_temperatures = f'{timestamp}: '
    row = [timestamp]
    for temperature in temperatures:
        row.append(temperature.actual)
        text_temperatures += f'{temperature.zone} ({temperature.actual} A'

        if temperature.target is not None:
            row.append(temperature.target)
            text_temperatures += f', {temperature.target} T'
        text_temperatures += ') '

    if  __simulation:
        __logger.info("[SIMULATED] %s", text_temperatures)
    else:
        __logger.debug(text_temperatures)
        writer.writerow(row)
        csv_file.close()


# if called directly then this is what will execute
if __name__ == "__main__":
    write(sys.argv[1], sys.argv[2])
