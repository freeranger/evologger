import urllib2
from config_helper import *

plugin_name = "Emoncms"
plugin_type = "output"

emon_logger = logging.getLogger('emoncms-plugin:')

invalidConfig = False

try:
    config = configparser.ConfigParser(allow_no_value=True)
    config.read('config.ini')

    emon_debug_enabled = is_debugging_enabled('Emoncms')
    emon_write_enabled = not get_boolean_or_default('Emoncms', 'Simulation', False)

    emon_api_key = config.get("Emoncms", "apiKey")
    emon_node_number = config.getint("Emoncms", "nodeNumber")

    emon_post_url='http://emoncms.org/input/post.json?apikey=' + emon_api_key + '&node=' + str(emon_node_number) + '&json={'

except Exception as e:
    emon_logger.error("Error reading config:\n%s", e)
    invalidConfig = True


def write(timestamp, temperatures):

    if invalidConfig:
        if emon_debug_enabled:
            emon_logger.debug('Invalid config, aborting write')
            return []

    debug_message = 'Writing to ' + plugin_name
    if not emon_write_enabled:
        debug_message += ' [SIMULATED]'
    emon_logger.debug(debug_message)

    debug_temperatures = '%s: ' % timestamp
    url = emon_post_url
    for temperature in temperatures:
        url = '%s%s Actual: %s,' % (url, temperature.zone, str(temperature.actual))
        debug_temperatures += "%s (%s A" % (temperature.zone, temperature.actual)
        if temperature.target is not None:
            url += ',%s Target: %s,' % (temperature.zone, str(temperature.target))
            debug_temperatures += ", %s T" % temperature.target

    url += '}'
    url = url.replace(",}", "}")
    url = url.replace(" ", "")
    debug_temperatures += ') '

    if emon_debug_enabled:
        emon_logger.debug(debug_temperatures)
        emon_logger.debug('URL:' + url)

    try:
        if emon_write_enabled:
            response = urllib2.urlopen(url)
            emon_logger.debug('response: ' + str(response))
    except Exception as e:
        emon_logger.exception("Emon API error - aborting write\n%s", e)


# if called directly then this is what will execute
if __name__ == "__main__":
    import sys
    write(sys.argv[1], sys.argv[2])
