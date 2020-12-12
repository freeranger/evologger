from config_helper import *
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

plugin_name = "InfluxDB"
plugin_type="output"

influx_logger = logging.getLogger('influx-plugin:')

invalidConfig = False

try:

    config = configparser.ConfigParser(allow_no_value=True)
    config.read('config.ini')

    influx_debug_enabled = is_debugging_enabled('InfluxDB')
    influx_write_enabled = not get_boolean_or_default('InfluxDB', 'Simulation', False)

    influx_hostname = config.get("InfluxDB", "hostname")
    influx_port = config.get("InfluxDB", "port")
    influx_database = config.get("InfluxDB", "database")
    influx_username = config.get("InfluxDB", "username")
    influx_password = config.get("InfluxDB", "password")

    if influx_debug_enabled:
        influx_logger.debug("Influx Host: %s:%s Database: %s", influx_hostname, influx_port, influx_database)

except Exception as e:
    influx_logger.error("Error reading config:\n%s", e)
    invalidConfig = True

def prep_record(time, zone, actual, target):
    record_actual = None
    record_target = None
    record_delta = None

    if actual is not None and actual != '':
        try:
            record_actual = {
                "measurement": "zone_temp.actual",
                "tags": {
                    "zone": zone,
                },
                "time": time,
                "fields": {
                    "value": float(actual)
                }
            }
        except Exception as e:
            print e

    if target is not None and target != '':
        try:
            record_target = {
                "measurement": "zone_temp.target",
                "tags": {
                    "zone": zone,
                },
                "time": time,
                "fields": {
                    "value": float(target)
                }
            }
        except Exception as e:
            print e

    if record_actual is not None and record_target is not None:
        record_delta = {
            "measurement": "zone_temp.delta",
            "tags": {
                "zone": zone,
            },
            "time": time,
            "fields": {
                "value": float(actual) - float(target)
            }
        }

    return record_actual, record_target, record_delta


def write(timestamp, temperatures):

    if invalidConfig:
        if influx_debug_enabled:
            influx_logger.debug('Invalid config, aborting write')
            return []

    debug_message = 'Writing to ' + plugin_name
    if not influx_write_enabled:
        debug_message += ' [SIMULATED]'
    influx_logger.debug(debug_message)

    influx_client = InfluxDBClient(influx_hostname, influx_port, influx_username, influx_password, influx_database)

    debug_row_text = '%s: ' % timestamp
    data = []
    for temperature in temperatures:

        record_actual, record_target, record_delta = prep_record(timestamp, temperature.zone,
                                                                 temperature.actual, temperature.target)

        if record_actual:
            data.append(record_actual)
        if record_target:
            data.append(record_target)
        if record_delta:
            data.append(record_delta)

        debug_row_text += "%s (%s A" % (temperature.zone, temperature.actual)
        if temperature.target is not None:
            debug_row_text += ", %s T" % temperature.target
        debug_row_text += ') '

    if influx_debug_enabled:
        influx_logger.debug(debug_row_text)

    try:
        if influx_write_enabled:
            influx_client.write_points(data)
    except InfluxDBClientError as e:
        influx_logger.error("\nInflux DB error - aborting write\n%s", e)
        print str(e)


# if called directly then this is what will execute
if __name__ == "__main__":
    import sys
    write(sys.argv[1], sys.argv[2])
