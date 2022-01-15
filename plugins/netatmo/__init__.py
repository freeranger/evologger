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

from config_helper import *
from Temperature import *

plugin_name = "Netatmo"
plugin_type = "input"

ssl._create_default_https_context = ssl._create_unverified_context
__STATION_TYPE = 'NAMain' # Indoor station type
__OUTDOOR_MODULE_TYPE = 'NAModule1' # Outdoor module type

__logger = get_plugin_logger(plugin_name)
__invalid_config = False


try:
    __config = get_config()
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)

    __section = __config[plugin_name]
    __client_id = __section['ClientId']
    __client_secret = __section['ClientSecret']
    __username = __section['Username']
    __password = __section['Password']

    if __config.has_option(plugin_name, "StationName"):
        __station_name = get_string_or_default(plugin_name, 'StationName', None)
    else:
        __station_name = None

    if __config.has_option(plugin_name, "OutDoorModule"):
        __module_name = get_string_or_default(plugin_name, 'OutdoorModule', None)
    else:
        __module_name = None

    __zone = get_string_or_default(plugin_name, 'Outside', 'Outside')

    if __station_name is None:
        __logger.debug("No station name supplied => use the first station of type: '%s' found", __STATION_TYPE)
    else:
        __logger.debug("Indoor Station: %s", __station_name)

    if __module_name is None:
        __logger.debug("No outdoor module name supplied => use the first module type: '%s' found attached to the station", __OUTDOOR_MODULE_TYPE)
    else:
        __logger.debug("Outdoor Module: %s", __module_name)

    __logger.debug("Outside Zone: %s", __zone)

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True

def _post_request(url: str, request_params):
    full_url = f'https://api.netatmo.com/{url}'
    params = parse.urlencode(request_params).encode('utf-8')
    __logger.debug(full_url)
    try:
        with requests.get(full_url, headers= {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
                },
                params=params, timeout=30) as response:
            response.raise_for_status()
            return response.json()
    except requests.HTTPError as err:
        __logger.exception(f'Netatmo API HTTPError {response.status_code} {response.reason} - aborting read\n{err}')
        return None
    except Exception as ex:
        __logger.exception("Exception processing request to %s - %s", url, str(ex))
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

    def __init__(self, client_id: str, client_secret: str, username: str, password: str) -> None:
        self.__logger = get_plugin_logger(f'{plugin_name}:{self.__class__.__name__}')
        self.__token_file = f'{gettempdir()}/{plugin_name}.access_tokens.json'
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__username = username
        self.__password = password

        try:
            # Fetch previously saved tokens we can reuse them
            with io.open(self.__token_file, 'r', encoding='UTF-8') as f:
                token_data = load(f)
                self.__access_token = token_data[0]
                self.__refresh_token = token_data[1]
                self.__access_token_expires = datetime.strptime(token_data[2], "%Y-%m-%d %H:%M:%S.%f")
            self.__logger.debug(f'Using cached credentials expiring at {self.__access_token_expires}')
        except (IOError, ValueError):
            self.__access_token = None
            self.__refresh_token = None
            self.__access_token_expires = datetime.utcnow() - timedelta(hours = 1)
            self.__logger.debug('No cached credentials available')


    def access_token(self) -> str:
        """
        Returns an access token for the Netatmo API
        """
        if self.__access_token_expires < datetime.utcnow():
            if self.__refresh_token is None:
                self.__logger.debug('No stored refresh token => Get new tokens using credentials')
                get_token_request = {
                                "grant_type" : "password",
                                "client_id" : self.__client_id,
                                "client_secret" : self.__client_secret,
                                "username" : self.__username,
                                "password" : self.__password,
                                "scope" : 'read_station'
                            }
            else:
                self.__logger.debug('Store refresh token found => Use this to get new tokens')
                get_token_request = {
                        "grant_type" : "refresh_token",
                        "refresh_token" : self.__refresh_token,
                        "client_id" : self.__client_id,
                        "client_secret" : self.__client_secret
                    }
            resp = _post_request('oauth2/token', get_token_request)
            if resp is not None:
                self.__access_token=resp['access_token']
                self.__refresh_token=resp['refresh_token']
                self.__access_token_expires = datetime.utcnow() + timedelta(seconds=int(resp['expire_in']))

                # save session-id's so we don't need to re-authenticate every polling cycle.
                with io.open(self.__token_file, "w", encoding='UTF-8') as f:
                    token_data = [ self.__access_token, self.__refresh_token, str(self.__access_token_expires) ]
                    dump(token_data, f)

                return self.__access_token

            # If we didn't get a valid response and we used a refresh token then we will try again gettng q brand new token
            if self.__refresh_token is not None:
                self.__refresh_token = None
                return self.access_token()
            return None

        self.__logger.debug('Existing valid token found => use this')
        return self.__access_token


def __find_station(stations):
    if __station_name is None:
        station = next((x for x in stations if x['type'] == __STATION_TYPE), None)
        find_by = f'type: {__STATION_TYPE}'
    else:
        station = next((x for x in stations if x['station_name'] == __station_name), None)
        find_by = f'name: {__station_name}'

    if station is None:
        station_names_and_types = { f"{d['station_name']} ({d['type']})" : d for d in stations }
        raise ModuleNotFound(f"Station not found by {find_by} - station list: [{', '.join(station_names_and_types)}]")

    return station


def __find_module(modules):
    if __module_name is None:
        module = next((x for x in modules if x['type'] == __OUTDOOR_MODULE_TYPE), None)
        find_by = f'type: {__OUTDOOR_MODULE_TYPE}'
    else:
        module = next((x for x in modules if x['module_name'] == __module_name), None)
        find_by = f'name: {__module_name}'

    if module is None:
        module_names_and_types = {', '.join({ f"{m['module_name']} ({m['type']})" : m for m in modules })}
        raise ModuleNotFound(f"Module not found by {find_by} - module list: [{module_names_and_types}]")

    return module


def read():
    """
    Reads the outside temperature from a Netatmo outdoor module
    """

    if __invalid_config:
        __logger.debug('Invalid config, aborting read')
        return []

    debug_message = f"Reading Temp for {__station_name if __station_name is not None else f'the first {__STATION_TYPE } station'} from the {__module_name if __module_name is not None else f'first {__OUTDOOR_MODULE_TYPE} outdoor' } module from {plugin_name}"
    if __simulation:
        debug_message += ' [SIMULATED]'
        __logger.debug(debug_message)

    if __simulation:
        debug_message += ' [SIMULATED]'
        __logger.debug(debug_message)
        temp = round(random.uniform(12.0, 23.0), 1)
        __logger.info(f'[SIMULATED] {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}: {__zone} ({temp})')
        return [Temperature(__zone, temp)]

    try:
        access_token = Authenticate(__client_id, __client_secret, __username, __password).access_token()
        if access_token is None:
            raise Exception('Failed to retrieve a valid access token')

        response = _post_request('api/getstationsdata', { 'access_token' : access_token })
        if response is None:
            raise Exception('Failed to retrieve station data')
        try:
            raw_data = response['body']['devices']

            station = __find_station(raw_data)
            module = __find_module(station['modules'])

            temp = round(module['dashboard_data']['Temperature'], 1)
            __logger.debug(f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}: {__zone} ({temp})')
            return [Temperature(__zone, temp)]

        except ModuleNotFound as mex:
            __logger.error('%s', mex)
        except Exception:
            __logger.exception('Failed to parse station/module data from %s', response)

    except requests.HTTPError as e:
        __logger.exception(f'Netatmo API HTTPError - aborting write\n{e}')
    except Exception as e:
        __logger.exception(f'Netatmo API error - aborting read:\n{e}')

    return []


# if called directly then this is what will execute
if __name__ == "__main__":
    read()
