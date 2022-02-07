"""
Console output plugin
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging

from AppConfig import AppConfig

def _get_plugin_logger(config: AppConfig, plugin_name: str) -> logging.Logger:
    """
    Gets a logger for the supplied plugin
    """
    logger = logging.getLogger(f'{plugin_name}-plugin')
    logger.setLevel(logging.DEBUG if config.is_debugging_enabled(plugin_name) else logging.INFO)
    return logger

class PluginBase(ABC):
    """Base class for all plugins"""

    _logger = None
    _invalid_config: bool = None
    _simulation: bool = None
    plugin_name:str = None
    plugin_type: str = None

    def __init__(self, config: AppConfig, plugin_name: str, plugin_type: str) -> None:
        super().__init__()
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type
        self._logger = _get_plugin_logger(config, plugin_name)
        self._invalid_config = False
        self._simulation = config.get_boolean_or_default(plugin_name, 'Simulation', False)

        try:
            self._read_configuration(config)
        except Exception as config_ex:
            self._logger.exception(f'Error reading config:\n{config_ex}')
            self._invalid_config = True

    @abstractmethod
    def _read_configuration(self, config: AppConfig):
        pass


class InputPluginBase(PluginBase):
    """Base class for all Input plugins"""

    @abstractmethod
    def _read_temperatures(self):
        """
        Subclass method to Read temperature(s) from an input source
        """

    def read(self):
        """
        Reads temperature(s) from an input source
        """

        if self._invalid_config:
            self._logger.debug('Invalid config, aborting read')
            return []

        debug_message = f'Reading temperatures from {self.plugin_name}'
        if self._simulation:
            debug_message += ' [SIMULATED]'
            self._logger.debug(debug_message)

        try:
            (temperatures, text_temperatures) = self._read_temperatures()
            text_temperatures = f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} {text_temperatures}'
            if self._simulation:
                self._logger.info(f'[SIMULATED] {text_temperatures}')
            else:
                self._logger.debug(text_temperatures)
            return temperatures
        except Exception:
            self._logger.exception('Error reading temperatures, aborting read')
            return []


class OutputPluginBase(PluginBase):
    """Base class for all output plugins"""

    @abstractmethod
    def _write_temperatures(self, timestamp, temperatures) -> str:
        """
        Implementations-specific temperature writer
        """

    def write(self, timestamp, temperatures):
        """
        Writes the teemperatures to an output destination
        """
        if self._invalid_config:
            self._logger.warning('Invalid config, aborting write')
            return

        debug_message = 'Writing temperatures to ' + self.plugin_name
        if self._simulation:
            debug_message += ' [SIMULATED]'
        self._logger.debug(debug_message)

        try:
            self._write_temperatures(timestamp, temperatures)
        except Exception:
            self._logger.exception('Error writing temperatures, aborting write')
