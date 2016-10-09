from evohomeclient2 import EvohomeClient
from Temperature import *
from config_helper import *
from datetime import datetime
import logging
import random

plugin_name = "EvoHome"
plugin_type = "input"

evohome_plugin_logger = logging.getLogger('evohome-plugin:')

invalidConfig = False

try:
    config = ConfigParser.ConfigParser(allow_no_value=True)
    config.read('config.ini')

    evohome_debug_enabled = is_debugging_enabled('EvoHome')
    evohome_read_enabled = not get_boolean_or_default('EvoHome', 'Simulation', False)
    evohome_http_debug_enabled = get_boolean_or_default('EvoHome', 'httpDebug', False)
    evohome_username = config.get("EvoHome", "username")
    evohome_password = config.get("EvoHome", "password")
    evohome_hotwater = config.get("EvoHome", "HotWater")

    if config.has_option("EvoHome", "HotWaterSetPoint"):
        hot_water_setpoint = config.getfloat("EvoHome", "HotWaterSetPoint")
    else:
        hot_water_setpoint = None

except Exception, e:
    evohome_plugin_logger.error("Error reading config:\n%s", e)
    invalidConfig = True


def is_hotwater_on(client):
    location = client.locations[0]
    status = location.status()
    if 'dhw' in status['gateways'][0]['temperatureControlSystems'][0]:
        evohome_plugin_logger.debug('DHW found')
        dhw = status['gateways'][0]['temperatureControlSystems'][0]['dhw']
        return dhw['stateStatus']['state'] == 'On'
    else:
        evohome_plugin_logger.debug('No DHW found')
        return False


def read():

    if invalidConfig:
        if evohome_debug_enabled:
            evohome_plugin_logger.debug('Invalid config, aborting read')
            return []

    debug_message = 'Reading from ' + plugin_name
    if not evohome_read_enabled:
        debug_message += ' [SIMULATED]'
        evohome_plugin_logger.debug(debug_message)

    client = None

    temperatures = []

    try:
        if evohome_read_enabled:
            # Evohome client turns off global debugging  it so we need to re-enable!
            global_debug = logging.getLogger().isEnabledFor(logging.DEBUG)
            client = EvohomeClient(evohome_username, evohome_password, debug=evohome_http_debug_enabled)
            if global_debug:
                logging.getLogger().setLevel(logging.DEBUG)
    except Exception, e:
        evohome_plugin_logger.error("EvoHome API error - aborting read\n%s", e)
        return []

    debug_temperatures = '%s: ' % datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    if evohome_read_enabled:

        try:
            zones = client.temperatures()
        except Exception, e:
            evohome_plugin_logger.error("EvoHome API error getting temperatures - aborting\n%s", e)
            return

        for zone in zones:
            # normalise response for DHW to be consistent with normal zones
            if zone['thermostat'] == 'DOMESTIC_HOT_WATER':
                zone['name'] = evohome_hotwater
                if is_hotwater_on(client):
                    if hot_water_setpoint is not None:
                        zone['setpoint'] = hot_water_setpoint
                else:
                    zone['setpoint'] = 0.0

            debug_temperatures += "%s (%s A" % (zone['name'], zone['temp'])

            if zone['setpoint'] != '':
                temp = Temperature(zone['name'], float(zone['temp']), float(zone['setpoint']))
                debug_temperatures += ", %s T" % zone['setpoint']
            else:
                temp = Temperature(zone['name'], float(zone['temp']))
            debug_temperatures += ') '
            temperatures.append(temp)
    else:
        temperatures = [Temperature("Lounge", round(random.uniform(12.0, 28.0), 1), 22.0),
                        Temperature("Master Bedroom", round(random.uniform(18.0, 25.0), 1), 12.0),
                        Temperature("_DHW", round(random.uniform(40, 65), 1))]
        debug_temperatures = '%s (%s A) (%s T) %s (%s A) (%s T) %s (%s A)' %\
                             (temperatures[0].zone, temperatures[0].actual, temperatures[0].target,
                              temperatures[1].zone, temperatures[1].actual, temperatures[1].target,
                              temperatures[2].zone, temperatures[2].actual)

    evohome_plugin_logger.debug(debug_temperatures)

    return temperatures


# if called directly then this is what will execute
if __name__ == "__main__":
    read()
