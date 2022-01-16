"""
Evohome input plugin - for getting all your zone and DHW temperatures
"""
# pylint: disable=C0103,C0301,R0913,W0212,W0703

from datetime import datetime
import json
import io
import logging
import random
from tempfile import gettempdir
from evohomeclient2 import EvohomeClient
from config_helper import *
from Temperature import *

plugin_name = "EvoHome"
plugin_type = "input"

__logger = get_plugin_logger(plugin_name)
__token_file = f'{gettempdir()}/{plugin_name}.access_tokens.json'
__invalid_config = False
_config = None

try:
    _config = get_config()
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)
    __http_debug_enabled = get_boolean_or_default(plugin_name, 'httpDebug', False)
    __section = _config[plugin_name]
    __username = __section['username']
    __password = __section['password']
    _location = get_string_or_default(plugin_name, 'Location', None)
    _hotwater = __section['HotWater']
    __hotwater_setpoint = get_float_or_default(plugin_name, 'HotWaterSetPoint', None)

except Exception as config_ex:
    __logger.error(f'Error reading config:\n{config_ex}')
    __invalid_config = True

class EvohomeMultiLocationClient(EvohomeClient):
    """
    Add to the base class the ability to get a specified location/heating system - for installations with multiple locations
    """

    def __init__(self, username:str, password:str, debug:bool=False, refresh_token=None, access_token=None, access_token_expires=None):
        super(EvohomeMultiLocationClient, self).__init__(username, password, debug, refresh_token, access_token, access_token_expires)
        self.__logger = get_plugin_logger(f'{plugin_name}:{self.__class__.__name__}')

    def get_location(self, locationId=None):
        """
        Get the location with the supplied name or id, or the first if none is specified
        """

        if locationId is None or locationId == '':
            self.__logger.debug('No location specified, returning the first one')
            return self.locations[0]

        actual_location = self._find_location_by_id(locationId)

        if actual_location is None:
            actual_location = self._find_location_by_name(locationId)

        if actual_location is None:
            raise ValueError(f'No location found with the id or name "{locationId}"') from None
        return actual_location


    def get_heating_system(self, locationId=None):
        """
        Get the heating system for the location with the supplied id or name, or for the first location if none is specified
        """

        location = self.get_location(locationId)

        if len(location._gateways) == 1:
            gateway = location._gateways[0]
        else:
            raise Exception(f'More than one gateway available - found {len(location._gateways)}') from None

        if len(gateway._control_systems) == 1:
            control_system = gateway._control_systems[0]
        else:
            raise Exception(f'More than one control system available - found {len(gateway._control_systems)}') from None

        return control_system


    def _find_location_by_id(self, locationId):
        matching_locations = list(filter(lambda l: l.locationId == locationId, self.locations))

        matching_locations_count = len(matching_locations)
        if matching_locations_count == 0:
            self.__logger.debug(f'Did not find locationId: {locationId}')
            return None
        if matching_locations_count == 1:
            self.__logger.debug(f'Found locationId: {locationId}')
            return matching_locations[0]
        raise ValueError(f'Found {matching_locations_count} locations matching "{locationId}"') from None


    def _find_location_by_name(self, name):
        matching_locations = list(filter(lambda l: l.name == name, self.locations))

        matching_locations_count = len(matching_locations)
        if matching_locations_count == 0:
            self.__logger.debug(f'Did not find location named: {name}')
            return None
        if matching_locations_count == 1:
            self.__logger.debug(f'Found location named: {name}')
        else:
            self.__logger.debug(f'Found {matching_locations_count} locations matching "{name}", returning the first one')
        return matching_locations[0]


def __is_hotwater_on(client) -> bool:
    """
    Determines if the hot water is on or not
    """
    location = client.get_location(_location)
    status = location.status()
    if 'dhw' in status['gateways'][0]['temperatureControlSystems'][0]:
        __logger.debug('DHW found')
        dhw = status['gateways'][0]['temperatureControlSystems'][0]['dhw']
        return dhw['stateStatus']['state'] == 'On'
    __logger.debug('No DHW found')
    return False


def __get_evoclient():
    """
    Returns an instance of an Evohome client which caches credentials
    """

    # The Evohome client library turns off global debugging  it so we need to re-enable!
    global_debug = logging.getLogger().isEnabledFor(logging.DEBUG)
    try:
        # Actually getting a token is rate-limited, though using it is not.
        # So we get and store tokens we can reuse them
        # https://github.com/watchforstock/evohome-client/issues/57
        with io.open(__token_file, "r", encoding='UTF-8') as f:
            token_data = json.load(f)
            access_token = token_data[0]
            refresh_token = token_data[1]
            access_token_expires = datetime.strptime(token_data[2], "%Y-%m-%d %H:%M:%S.%f")
        __logger.debug(f'Using cached credentials expiring at {access_token_expires}')
    except (IOError, ValueError):
        access_token = None
        refresh_token = None
        access_token_expires = None
        __logger.debug('No cached credentials available')

    client = EvohomeMultiLocationClient(__username, __password, debug=__http_debug_enabled, refresh_token=refresh_token, access_token=access_token, access_token_expires=access_token_expires)
    if global_debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # save session-id's so we don't need to re-authenticate every polling cycle.
    with io.open(__token_file, "w", encoding='UTF-8') as f:
        token_data = [ client.access_token, client.refresh_token, str(client.access_token_expires) ]
        json.dump(token_data, f)

    return client


def read():
    """
    Reads the temperatures from an EvoHome instance
    """

    if __invalid_config:
        __logger.warning('Invalid config, aborting read')
        return []

    debug_message = f'Reading from {plugin_name}'
    if __simulation:
        debug_message += ' [SIMULATED]'
        __logger.debug(debug_message)

    client = None

    temperatures = []

    try:
        if not __simulation:
            client = __get_evoclient()
    except Exception as e:
        __logger.exception(f'EvoHome API error - aborting read\n{e}')
        return []

    text_temperatures = f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} '

    if not __simulation:

        try:
            if _location is None:
                __logger.debug('No location specified, will use the first by default')
            else:
                __logger.debug(f'Getting data for location: {_location}')

            zones = client.get_heating_system(_location).temperatures()
        except Exception as e:
            __logger.exception(f'EvoHome API error getting temperatures - aborting\n{e}')
            return []

        for zone in zones:
            # normalise response for DHW to be consistent with normal zones
            if zone['thermostat'] == 'DOMESTIC_HOT_WATER':
                zone['name'] = _hotwater
                if __is_hotwater_on(client):
                    if __hotwater_setpoint is not None:
                        zone['setpoint'] = __hotwater_setpoint
                else:
                    zone['setpoint'] = 0.0

            text_temperatures += f'{zone["name"]} ({zone["temp"]} A'

            # Handle a bug mentioned here https://www.automatedhome.co.uk/vbulletin/showthread.php?4696-Beginners-guide-to-graphing-Evohome-temperatures-using-python-and-plot-ly/page6
            # Not sure if 128 is reported or not a number at all so deal with both...

            def temp_or_default(raw_temp):
                DEFAULT_TEMP = 0.0
                try:
                    temp = float(raw_temp)
                    if temp == 128.0:
                        __logger.warning(f'No temperature returned for Zone: {zone["name"]} - returning default ({DEFAULT_TEMP}')
                        return DEFAULT_TEMP
                    return temp
                except Exception:
                    __logger.exception(f'Error converting "{raw_temp}" to a float, returning default ({DEFAULT_TEMP}')
                    return DEFAULT_TEMP

            if zone['setpoint'] != '' and zone['setpoint'] is not None:
                temp = Temperature(zone['name'], temp_or_default(zone['temp']), temp_or_default(zone['setpoint']))
                text_temperatures += f', {zone["setpoint"]} T'
            else:
                temp = Temperature(zone['name'], temp_or_default(zone['temp']))
            text_temperatures += ') '
            temperatures.append(temp)
            __logger.debug(text_temperatures)
    else:
        # Return some random temps if simulating a read
        temperatures = [Temperature("Lounge", round(random.uniform(12.0, 28.0), 1), 22.0),
                        Temperature("Master Bedroom", round(random.uniform(18.0, 25.0), 1), 12.0),
                        Temperature(_hotwater, round(random.uniform(40, 65), 1))]
        text_temperatures = f'[SIMULATED] {temperatures[0].zone} ({temperatures[0].actual} A) ({temperatures[0].target} T) {temperatures[1].zone} ({temperatures[1].actual} A) ({temperatures[1].target} T) {temperatures[2].zone} ({temperatures[2].actual} A)'
        __logger.info(text_temperatures)

    return temperatures


# if called directly then this is what will execute
if __name__ == "__main__":
    read()
