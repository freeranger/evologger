"""
InfluxDB v1.x input plugin
"""
# pylint: disable=W0406

import sys
import urllib.parse
from influxdb import InfluxDBClient, exceptions
from config_helper import *

plugin_name = "InfluxDB"
plugin_type="output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)
    __section = get_config()[plugin_name]
    __hostname = __section["hostname"]
    __port = __section["port"]
    __database = __section["database"]
    __username = __section["username"]
    __password = __section["password"]

    __logger.debug(f'Influx Host: {__hostname}:{__port} Database: {__database}')

except Exception as config_ex:
    __logger.exception("Error reading config:\n%s", config_ex)
    __invalid_config = True


def get_zone_measurements(time, zone, actual, target):
    """
    Returns the actual, target, and delta data points for a zone
    """

    record_actual = None
    record_target = None
    record_delta = None

    def create_point(name: str, value: float):
        try:
            return {
                    "measurement": name,
                    "tags": {
                        "zone": zone,
                    },
                    "time": time,
                    "fields": {
                        "value": value
                    }
                }
        except Exception as e:
            __logger.exception(f'Error creating data point for {name}, zone: {zone}, value: {value}:\n{e}')
            return {}

    if actual is not None and actual != '':
        record_actual = create_point("zone_temp.actual", float(actual))

    if target is not None and target != '':
        record_target = create_point("zone_temp.target", float(target))

    if record_actual is not None and record_target is not None:
        record_delta = create_point("zone_temp.delta", float(actual) - float(target))

    return record_actual, record_target, record_delta


def write(timestamp, temperatures):
    """
    Writes the temperatures to the database
    """

    if __invalid_config:
        __logger.warning('Invalid config, aborting write')

    debug_message = f'Writing to {plugin_name}'
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    influx_client = InfluxDBClient(__hostname, __port, __username, __password, __database)

    debug_row_text = f'{timestamp}: '
    data = []
    for temperature in temperatures:

        record_actual, record_target, record_delta = get_zone_measurements(timestamp, temperature.zone, temperature.actual, temperature.target)

        if record_actual:
            data.append(record_actual)
        if record_target:
            data.append(record_target)
        if record_delta:
            data.append(record_delta)

        debug_row_text += f'{temperature.zone} ({temperature.actual} A'
        if temperature.target is not None:
            debug_row_text += f', {temperature.target} T'
        debug_row_text += ') '

    try:
        if __simulation:
            __logger.info("[SIMULATED] %s", debug_row_text)
        else:
            __logger.debug(debug_row_text)
            __logger.debug('Writing all zone measurements to influx...')
            influx_client.write_points(data)
    except Exception as e:
        if hasattr(e, 'request'):
            __logger.exception(f'Error Writing to {__database} at {__hostname}:{__port} - aborting write.\nRequest: {e.request.method} {urllib.parse.unquote(e.request.url)}\nBody: {e.request.body}.\nResponse: {e.response}\nError:{e}')
        else:
            __logger.exception(f'Error Writing to {__database} at {__hostname}:{__port} - aborting write\nError:{e}')


# if called directly then this is what will execute
if __name__ == "__main__":
    write(sys.argv[1], sys.argv[2])
