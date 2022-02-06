"""
Evohome input plugin - for getting all your zone and DHW temperatures
"""
# pylint: disable=R0913,W0212

from datetime import datetime
import json
import http # Need this for disabling http debugging if necessary
import io
import logging
import random
from tempfile import gettempdir
import requests
from evohomeclient2 import EvohomeClient

from AppConfig import AppConfig
from plugins.PluginBase import InputPluginBase, _get_plugin_logger
from Temperature import *


class EvohomeMultiLocationClient(EvohomeClient):
    """
    Add to the base class the ability to get a specified location/heating system - for installations with multiple locations
    """

    def __init__(self, config: AppConfig, plugin_name, username:str, password:str, debug:bool=False, refresh_token=None, access_token=None, access_token_expires=None):
        super().__init__(username, password, debug, refresh_token, access_token, access_token_expires)
        self._logger = _get_plugin_logger(config, f'{plugin_name}:{self.__class__.__name__}')


    def get_location(self, locationId=None):
        """
        Get the location with the supplied name or id, or the first if none is specified
        """

        if locationId is None or locationId == '':
            # No location specified, returning the first one
            return self.locations[0]

        actual_location = self._find_location_by_id(locationId)

        if actual_location is None:
            actual_location = self._find_location_by_name(locationId)

        if actual_location is None:
            raise ValueError(f'No location found with the id or name "{locationId}"') from None

        self._logger.debug(f'Location {actual_location} found')
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
            self._logger.debug(f'Did not find locationId: {locationId}')
            return None
        if matching_locations_count == 1:
            self._logger.debug(f'Found locationId: {locationId}')
            return matching_locations[0]
        raise ValueError(f'Found {matching_locations_count} locations matching "{locationId}"') from None


    def _find_location_by_name(self, name):
        matching_locations = list(filter(lambda l: l.name == name, self.locations))

        matching_locations_count = len(matching_locations)
        if matching_locations_count == 0:
            self._logger.debug(f'Did not find location named: {name}')
            return None
        if matching_locations_count == 1:
            self._logger.debug(f'Found location named: {name}')
        else:
            self._logger.debug(f'Found {matching_locations_count} locations matching "{name}", returning the first one')
        return matching_locations[0]

class Plugin(InputPluginBase):
    """Evohome input Plugin immplementation"""

    # pylint: disable=too-many-instance-attributes

    def _read_configuration(self, config: AppConfig):
        self._config = config
        section = config[self.plugin_name]
        self._token_file = f'{gettempdir()}/{self.plugin_name}.access_tokens.json'
        self._http_debug = config.get_boolean_or_default('DEFAULT', 'httpDebug', False)
        self._username = section['username']
        self._password = section['password']
        self._location = config.get_string_or_default(self.plugin_name, 'Location', None)
        if self._location is None:
            self._logger.debug('No location specified, will use the first by default')
        else:
            self._logger.debug(f'Using location: {self._location}')

        self._hotwater = section['HotWater']
        self._hotwater_setpoint = config.get_float_or_default(self.plugin_name, 'HotWaterSetPoint', None)


    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'EvoHome', 'input')

    def _get_evoclient(self):
        """
        Returns an instance of an Evohome client which caches credentials
        """

        # The Evohome client library turns off global debugging so save the value incase we need to re-enable!
        global_debug = logging.getLogger().isEnabledFor(logging.DEBUG)
        try:
            self._logger.debug(f'Reading token cache from {self._token_file}')
            # Actually getting a token is rate-limited, though using it is not.
            # So we get and store tokens we can reuse them
            # https://github.com/watchforstock/evohome-client/issues/57
            with io.open(self._token_file, "r", encoding='UTF-8') as f:
                token_data = json.load(f)
                access_token = token_data[0]
                refresh_token = token_data[1]
                access_token_expires = datetime.strptime(token_data[2], "%Y-%m-%d %H:%M:%S.%f")
            self._logger.debug(f'Using cached credentials expiring at {access_token_expires}')
        except (IOError, ValueError):
            access_token = None
            refresh_token = None
            access_token_expires = None
            self._logger.debug('No cached credentials available')

        client = EvohomeMultiLocationClient(self._config, self.plugin_name, self._username, self._password, debug=self._config.is_debugging_enabled(self.plugin_name) , refresh_token=refresh_token, access_token=access_token, access_token_expires=access_token_expires)
        if global_debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # EvohomeClient turns on http debug logging if debug is set - we only want it if we have http debug enabled
        if self._config.is_debugging_enabled(self.plugin_name) is True and self._http_debug is False:
            http.client.HTTPConnection.debuglevel = 0

        # save session-id's so we don't need to re-authenticate every polling cycle.
        with io.open(self._token_file, "w", encoding='UTF-8') as f:
            token_data = [ client.access_token, client.refresh_token, str(client.access_token_expires) ]
            json.dump(token_data, f)

        return client

    def _get_raw_data(self, client):
        """
        Get the same temp data that EvoClient pulls back for debugging/error diagnostics
        """
        location =  client.get_location(self._location)
        r = requests.get(f'https://tccna.honeywell.com/WebAPI/emea/api/v1/location/{location.locationId}/status?includeTemperatureControlSystems=True', headers=client._headers())
        return r.text


    def _is_hotwater_on(self, client) -> bool:
        """
        Determines if the hot water is on or not
        """
        location = client.get_location(self._location)
        status = location.status()
        if 'dhw' in status['gateways'][0]['temperatureControlSystems'][0]:
            self._logger.debug('DHW found')
            dhw = status['gateways'][0]['temperatureControlSystems'][0]['dhw']
            return dhw['stateStatus']['state'] == 'On'
        self._logger.debug('No DHW found')
        return False

    # pylint disable=E1101
    def _read_temperatures(self):
        """
        Reads the temperatures from an EvoHome instance
        """

        client = None
        temperatures = []

        try:
            if not self._simulation:
                client = self._get_evoclient()
        except Exception as e:
            self._logger.exception(f'EvoHome API error - aborting read\n{e}')
            return ([], '')

        text_temperatures = ''

        if self._simulation:
            # Return some random temps if simulating a read
            temperatures = [Temperature("Lounge", round(random.uniform(12.0, 28.0), 1), 22.0),
                            Temperature("Master Bedroom", round(random.uniform(18.0, 25.0), 1), 12.0),
                            Temperature(self._hotwater, round(random.uniform(40, 65), 1))]
            text_temperatures = f'[SIMULATED] {temperatures[0].zone} ({temperatures[0].actual} A) ({temperatures[0].target} T) {temperatures[1].zone} ({temperatures[1].actual} A) ({temperatures[1].target} T) {temperatures[2].zone} ({temperatures[2].actual} A)'
            self._logger.info(text_temperatures)

            return (temperatures, text_temperatures)

        try:
            heating_system = client.get_heating_system(self._location)
            zones = heating_system.temperatures()
        except Exception as e:
            self._logger.exception(f'EvoHome API error getting temperatures - aborting\n{e}')
            return ([], '')

        while True:
            try:
                zone = next(zones)
                if isinstance(zone, KeyError):
                    if heating_system.hotwater is not None:
                        self._logger.exception(f'EvoHome API key error getting temperatures - could be hot water- status: {heating_system.hotwater.temperatureStatus} - skipping\n{zone}\nraw_data={self._get_raw_data(client)}')
                    else:
                        self._logger.exception(f'EvoHome API key error getting temperatures - skipping\n{zone}\nraw_data={self._get_raw_data(client)}')
                else:
                    if isinstance(zone, Exception):
                        self._logger.exception(f'EvoHome API error getting temperatures - skipping\n{zone}\nraw_data={self._get_raw_data(client)}')
            except StopIteration:
                break
            except Exception as ex:
                self._logger.exception(f'EvoHome API error getting temperatures - skipping\n{ex}\nraw_data={self._get_raw_data(client)}')
            else:
                # normalise response for DHW to be consistent with normal zones
                if zone['thermostat'] == 'DOMESTIC_HOT_WATER':
                    zone['name'] = self._hotwater
                    if self._is_hotwater_on(client):
                        if self._hotwater_setpoint is not None:
                            zone['setpoint'] = self._hotwater_setpoint
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
                            self._logger.warning(f'No temperature returned for Zone: {zone["name"]} - returning default ({DEFAULT_TEMP}')  # pylint disable=W0640
                            return DEFAULT_TEMP
                        return temp
                    except Exception:
                        self._logger.exception(f'Error converting "{raw_temp}" to a float, returning default ({DEFAULT_TEMP}')
                        return DEFAULT_TEMP

                if zone['setpoint'] != '' and zone['setpoint'] is not None:
                    temp = Temperature(zone['name'], temp_or_default(zone['temp']), temp_or_default(zone['setpoint']))
                    text_temperatures += f', {zone["setpoint"]} T'
                else:
                    temp = Temperature(zone['name'], temp_or_default(zone['temp']))
                text_temperatures += ') '
                temperatures.append(temp)
                self._logger.debug(text_temperatures)

        return (temperatures, text_temperatures)
