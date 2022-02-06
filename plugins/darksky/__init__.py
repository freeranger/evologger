"""
DarkSky input plugin - for getting the outside temperature
"""

import random
import urllib.parse
import forecastio

from AppConfig import AppConfig
from plugins.PluginBase import InputPluginBase
from Temperature import *

class Plugin(InputPluginBase):
    """DarkSky input Plugin immplementation"""

    def _read_configuration(self, config: AppConfig):
        section = config[self.plugin_name]
        self._api_key = section['apiKey']
        self._latitude = section['latitude']
        self._longitude = section['longitude']
        self._zone = config.get_string_or_default(self.plugin_name, 'Outside', 'Outside')
        self._logger.debug("Outside Zone: %s", self._zone)

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'DarkSky', 'input')

    # pylint disable=E1101
    def _read_temperatures(self):
        """
        Reads the outside temperature from DarkSky
        """

        if not self._simulation:
            try:
                forecast = forecastio.load_forecast(self._api_key, self._latitude, self._longitude)
            except Exception as e:
                if hasattr(e, 'request'):
                    self._logger.exception(f'DarkSky API Error reading from {e.request.method} {urllib.parse.unquote(e.request.url)}\nResponse: {e.response.json()}\nError:{e}')
                else:
                    self._logger.exception(f'DarkSky API error - aborting read:\n{e}')
                return []

            temp = round(forecast.currently().temperature, 1) # pylint: disable=no-member
        else:
            temp = round(random.uniform(12.0, 23.0), 1)

        text_temperatures = f'{self._zone} ({temp})'

        return ([Temperature(self._zone, temp)], text_temperatures)
