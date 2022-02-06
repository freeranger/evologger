"""
Netatmo input plugin - for getting the outside temperature
"""
# pylint: disable=W0212

from datetime import datetime,timedelta
import io
from json import dump,load
import random
import ssl
from tempfile import gettempdir
from urllib import parse
import requests

from AppConfig import AppConfig
from plugins.PluginBase import InputPluginBase, _get_plugin_logger
from Temperature import *

ssl._create_default_https_context = ssl._create_unverified_context
_STATION_TYPE = 'NAMain' # Indoor station type
_OUTDOOR_MODULE_TYPE = 'NAModule1' # Outdoor module type


def _post_request(url: str, request_params, logger):
    full_url = f'https://api.netatmo.com/{url}'
    params = parse.urlencode(request_params).encode('utf-8')
    logger.debug(full_url)
    try:
        with requests.post(full_url, headers= {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
                },
                data=params, timeout=30) as response:
            response.raise_for_status()
            return response.json()
    except requests.HTTPError as err:
        logger.exception(f'HTTPError at {full_url} - {err.response.status_code} {err.response.reason} {err.response.json()} - aborting read\nError: {err}')
        return None
    except Exception as e:
        if hasattr(e, 'response'):
            logger.exception(f'Error at {full_url} {e.response.status_code} {e.response.reason} {e.response.json()} - aborting read\nError: {e}')
        else:
            logger.exception(f'Error at {full_url}\nError:{e}')
        return None

# pylint: disable=R0903
class ModuleNotFound(Exception):
    """
    Exception thrown when the configured station/module is not found in the response from the API
    """


# pylint: disable=R0902
class Authenticate:
    """
    Manages Netatmo authentication tokens
    """

    # pylint: disable=too-many-arguments
    def __init__(self, config: AppConfig, plugin_name, client_id: str, client_secret: str, username: str, password: str) -> None:
        self._logger = _get_plugin_logger(config, f'{plugin_name}:{self.__class__.__name__}')
        self._token_file = f'{gettempdir()}/{plugin_name}.access_tokens.json'
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password

        try:
            # Fetch previously saved tokens we can reuse them
            with io.open(self._token_file, 'r', encoding='UTF-8') as f:
                token_data = load(f)
                self._access_token = token_data[0]
                self._refresh_token = token_data[1]
                self._access_token_expires = datetime.strptime(token_data[2], "%Y-%m-%d %H:%M:%S.%f")
            self._logger.debug(f'Using cached credentials expiring at {self._access_token_expires}')
        except (IOError, ValueError):
            self._access_token = None
            self._refresh_token = None
            self._access_token_expires = datetime.utcnow() - timedelta(hours = 1)
            self._logger.debug('No cached credentials available')


    def access_token(self) -> str:
        """
        Returns an access token for the Netatmo API
        """
        if self._access_token_expires < datetime.utcnow():
            if self._refresh_token is None:
                self._logger.debug('No stored refresh token => Get new tokens using credentials')
                get_token_request = {
                                "grant_type" : "password",
                                "client_id" : self._client_id,
                                "client_secret" : self._client_secret,
                                "username" : self._username,
                                "password" : self._password,
                                "scope" : 'read_station'
                            }
            else:
                self._logger.debug('Store refresh token found => Use this to get new tokens')
                get_token_request = {
                        "grant_type" : "refresh_token",
                        "refresh_token" : self._refresh_token,
                        "client_id" : self._client_id,
                        "client_secret" : self._client_secret
                    }
            resp = _post_request('oauth2/token', get_token_request, self._logger)
            if resp is not None:
                self._access_token=resp['access_token']
                self._refresh_token=resp['refresh_token']
                self._access_token_expires = datetime.utcnow() + timedelta(seconds=int(resp['expire_in']))

                # save session-id's so we don't need to re-authenticate every polling cycle.
                with io.open(self._token_file, "w", encoding='UTF-8') as f:
                    token_data = [ self._access_token, self._refresh_token, str(self._access_token_expires) ]
                    dump(token_data, f)

                return self._access_token

            # If we didn't get a valid response and we used a refresh token then we will try again gettng q brand new token
            if self._refresh_token is not None:
                self._refresh_token = None
                return self.access_token()
            return None

        self._logger.debug('Existing valid token found => use this')
        return self._access_token


class Plugin(InputPluginBase):
    """Netatmo outdoor module input Plugin immplementation"""

    def _read_configuration(self, config: AppConfig):
        self._config = config
        section = config[self.plugin_name]
        self._client_id = section['ClientId']
        self._client_secret = section['ClientSecret']
        self._username = section['Username']
        self._password = section['Password']

        if config.has_option(self.plugin_name, "StationName"):
            self._station_name = config.get_string_or_default(self.plugin_name, 'StationName', None)
        else:
            self._station_name = None

        if config.has_option(self.plugin_name, "OutDoorModule"):
            self._module_name = config.get_string_or_default(self.plugin_name, 'OutdoorModule', None)
        else:
            self._module_name = None

        self._zone = config.get_string_or_default(self.plugin_name, 'Outside', 'Outside')

        if self._station_name is None:
            self._logger.debug("No station name supplied => use the first station of type: '%s' found", _STATION_TYPE)
        else:
            self._logger.debug("Indoor Station: %s", self._station_name)

        if self._module_name is None:
            self._logger.debug("No outdoor module name supplied => use the first module type: '%s' found attached to the station", _OUTDOOR_MODULE_TYPE)
        else:
            self._logger.debug("Outdoor Module: %s", self._module_name)

        self._logger.debug("Outside Zone: %s", self._zone)

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'Netatmo', 'input')

    def _find_station(self, stations):
        if self._station_name is None:
            station = next((x for x in stations if x['type'] == _STATION_TYPE), None)
            find_by = f'type: {_STATION_TYPE}'
        else:
            station = next((x for x in stations if x['station_name'] == self._station_name), None)
            find_by = f'name: {self._station_name}'

        if station is None:
            station_names_and_types = { f"{d['station_name']} ({d['type']})" : d for d in stations }
            raise ModuleNotFound(f"Station not found by {find_by} - station list: [{', '.join(station_names_and_types)}]")

        return station

    def _find_module(self, modules):
        if self._module_name is None:
            module = next((x for x in modules if x['type'] == _OUTDOOR_MODULE_TYPE), None)
            find_by = f'type: {_OUTDOOR_MODULE_TYPE}'
        else:
            module = next((x for x in modules if x['module_name'] == self._module_name), None)
            find_by = f'name: {self._module_name}'

        if module is None:
            module_names_and_types = {', '.join({ f"{m['module_name']} ({m['type']})" : m for m in modules })}
            raise ModuleNotFound(f"Module not found by {find_by} - module list: [{module_names_and_types}]")

        return module

    # pylint disable=E1101
    def _read_temperatures(self):
        """
        Reads the outside temperature from a Netatmo outdoor module
        """

        debug_message = f"Reading Temp for {self._station_name if self._station_name is not None else f'the first {_STATION_TYPE } station'} from the {self._module_name if self._module_name is not None else f'first {_OUTDOOR_MODULE_TYPE} outdoor' } module from {self.plugin_name}"
        if self._simulation:
            debug_message += ' [SIMULATED]'
            self._logger.debug(debug_message)

            temp = round(random.uniform(12.0, 23.0), 1)
            text_temperatures = f'{self._zone} ({temp})'
            return ([Temperature(self._zone, temp)], text_temperatures)

        try:
            access_token = Authenticate(self._config, self.plugin_name, self._client_id, self._client_secret, self._username, self._password).access_token()
            if access_token is None:
                raise Exception('Failed to retrieve a valid access token')

            response = _post_request('api/getstationsdata', { 'access_token' : access_token }, self._logger)
            if response is None:
                raise Exception('Failed to retrieve station data')
            try:
                raw_data = response['body']['devices']

                station = self._find_station(raw_data)
                module = self._find_module(station['modules'])

                temp = round(module['dashboard_data']['Temperature'], 1)

                text_temperatures = f'{self._zone} ({temp})'
                return ([Temperature(self._zone, temp)], text_temperatures)

            except ModuleNotFound as mex:
                self._logger.error('%s', mex)
            except Exception:
                self._logger.exception('Failed to parse station/module data from %s', response)

        except requests.HTTPError as e:
            self._logger.exception(f'Netatmo API HTTPError - aborting read\n{e}')
        except Exception as e:
            self._logger.exception(f'Netatmo API error - aborting read:\n{e}')

        return ([], '')
