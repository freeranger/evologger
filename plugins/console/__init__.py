"""
Console output plugin
"""

from AppConfig import AppConfig
from plugins.PluginBase import OutputPluginBase

class Plugin(OutputPluginBase):
    """Console output Plugin immplementation"""
    def _read_configuration(self, config: AppConfig):
        self._hot_water = config.get_string_or_default('DEFAULT', 'HotWater', None)

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'Console', 'output')

    def _write_temperatures(self, timestamp, temperatures):
        """
        Writes the temperatures to the console
        """

        text_temperatures = ''
        for t in temperatures:
            text_temperatures += f'{t.zone} ({t.actual}'

            if t.target is not None:
                text_temperatures += ' A'
                if t.zone == self._hot_water and t.target == 0.0:
                    text_temperatures += ', OFF'
                else:
                    text_temperatures += f', {t.target} T'
            text_temperatures += ') '

        if self._simulation is False:
            print (text_temperatures)

        return text_temperatures
