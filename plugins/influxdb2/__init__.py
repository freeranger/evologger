"""
InfluxDB v2.x input plugin
"""

import sys
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS
from config_helper import *

plugin_name = "InfluxDB2"
plugin_type="output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)
    __section = get_config()[plugin_name]
    __hostname = __section["hostname"]
    __port = __section["port"]
    __org = __section["org"]
    __bucket = __section["bucket"]
    __apikey = __section["apikey"]

    __logger.debug(f'Influx Host: {__hostname}:{__port} Org: {__org}, Bucket:{__bucket}')

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
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
            return Point(name).time(time).tag("zone", zone).field("value", value)
        except Exception as e:
            __logger.exception(f'Error creating data point for {name}, zone: {zone}, value: {value}:\n{e}')
            return Point(name)

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
        return

    debug_message = f'Writing to {plugin_name}'
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    influx_client = InfluxDBClient(url=f'{__hostname}:{__port}', token=__apikey, org=__org)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

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
            write_api.write(bucket=__bucket, record=data)
    except InfluxDBError as e:
        __logger.exception(f'Influx DB error - aborting write\n{e}')
        if e.response.status == 401:
            __logger.exception(f'Insufficient write permissions to Bucket: "{__bucket}" - aborting write\n{e}')
            raise Exception(f'Insufficient write permissions to Bucket: {__bucket}.') from e
        __logger.exception(f'Influx DB error - aborting write\n{e}')
        raise
    except Exception as e:
        __logger.exception(f'Error - aborting write\n{e}')


# if called directly then this is what will execute
if __name__ == "__main__":
    write(sys.argv[1], sys.argv[2])
