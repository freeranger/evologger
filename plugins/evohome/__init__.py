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
    evohome_location = get_string_or_default("EvoHome", "Location", None)

    if config.has_option("EvoHome", "HotWaterSetPoint"):
        hot_water_setpoint = config.getfloat("EvoHome", "HotWaterSetPoint")
    else:
        hot_water_setpoint = None

except Exception, e:
    evohome_plugin_logger.error("Error reading config:\n%s", e)
    invalidConfig = True

# Add to the base class the ability to get a specified location/heating system - for installations with multiple locations
class EvohomeMultiLocationClient(EvohomeClient):
    def __init__(self, username, password, debug=False):
        super(EvohomeMultiLocationClient, self).__init__(username, password, debug)

    # Get the location with the supplied name or id, or the first if none is specified
    def get_location(self, locationId=None):
        if locationId is None:
            evohome_plugin_logger.debug('No location specified, returning the first one')
            return self.locations[0]

        actual_location = self._find_location_by_id(locationId)

        if actual_location is None:
            actual_location = self._find_location_by_name(locationId)

        if actual_location is None:
            raise ValueError('No location found with the id or name "%s"' % locationId)
        return actual_location

    # Get the heating system for the location with the supplied id or name, or for the first location if none is specified
    def get_heating_system(self, locationId=None):
        location = self.get_location(locationId)

        if len(location._gateways) == 1:
            gateway = location._gateways[0]
        else:
            raise Exception("More than one gateway available")

        if len(gateway._control_systems) == 1:
            control_system = gateway._control_systems[0]
        else:
            raise Exception("More than one control system available")

        return control_system


    def _find_location_by_id(self, locationId):
        matching_locations = filter(lambda l: l.locationId == locationId, self.locations)

        matching_locations_count = len(matching_locations)
        if matching_locations_count == 0:
            evohome_plugin_logger.debug('Did not find locationId: %s' % locationId)
            return None
        elif matching_locations_count == 1:
            evohome_plugin_logger.debug('Found locationId: %s' % locationId)
            return matching_locations[0]
        else:
            raise ValueError('Found %d locations matching "%s"' % locationId)


    def _find_location_by_name(self, name):
        matching_locations = filter(lambda l: l.name == name, self.locations)

        matching_locations_count = len(matching_locations)
        if matching_locations_count == 0:
            evohome_plugin_logger.debug('Did not find location named: %s' % name)
            return None
        elif matching_locations_count == 1:
            evohome_plugin_logger.debug('Found location named: %s' % name)
        else:
            evohome_plugin_logger.debug('Found %d locations matching "%s", returning the first one' % (matching_locations_count, name))
        return matching_locations[0]



def is_hotwater_on(client):
    location = client.get_location(evohome_location)
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
            client = EvohomeMultiLocationClient(evohome_username, evohome_password, debug=evohome_http_debug_enabled)
            if global_debug:
                logging.getLogger().setLevel(logging.DEBUG)
    except Exception, e:
        evohome_plugin_logger.error("EvoHome API error - aborting read\n%s", e)
        return []

    debug_temperatures = '%s: ' % datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    if evohome_read_enabled:

        try:
            if evohome_location is None:
                evohome_plugin_logger.debug('No location specified, will use the first by default')
            else:
                evohome_plugin_logger.debug('Getting data for location: %s', evohome_location)

            zones = client.get_heating_system(evohome_location).temperatures()
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
