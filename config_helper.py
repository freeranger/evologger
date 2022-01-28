"""
Helpers for configuring the app/plugins
"""

from configparser import ConfigParser
import logging

__config_logger = logging.getLogger(__name__)

__config = ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
__config.read('config.ini')


def get_config() -> ConfigParser:
    """
    Returns the configuration read from config.ini
    """
    return __config


def get_boolean_or_default(section_name: str, option_name: str, default_value: bool) -> bool:
    """Gets a boolean value from config or returns the default value if not found

    Args:
        section_name (str): The section name
        option_name (str): The option name (key) in the section
        default_value (bool): The default value to return if the config value does not exist

    Returns:
        bool: The boolean value of the supplied option or the default value if it does not exist
    """

    __config_logger.debug("get_boolean_or_default(%s, %s, %s)", section_name, option_name, default_value)
    if __config.has_option(section_name, option_name):
        value = __config.get(section_name, option_name)

        return True if value is None else value.lower() == 'true'
    return default_value


def get_float_or_default(section_name: str, option_name: str, default_value: float) -> float:
    """Gets a float value from config or returns the default value if not found

    Args:
        section_name (str): The section name
        option_name (str): The option name (key) in the section
        default_value (float): The default value to return if the config value does not exist

    Returns:
        bool: The flot value of the supplied option or the default value if it does not exist
    """

    __config_logger.debug("get_float_or_default(%s, %s, %s)", section_name, option_name, default_value)

    if __config.has_option(section_name, option_name):
        value = __config.getfloat(section_name, option_name)
        return value
    return default_value


def get_string_or_default(section_name: str, option_name: str, default_value: str) -> str:
    """Gets a string value from config or returns the default value if not found

    Args:
        section_name (str): The section name
        option_name (str): The option name (key) in the section
        default_value (str): The default value to return if the config vlaue does not exist

    Returns:
        str: The string value of the supplied option or the default value if it does not exist
    """

    __config_logger.debug("get_string_or_default(%s, %s, %s)", section_name, option_name, default_value)

    if __config.has_option(section_name, option_name):
        value = __config.get(section_name, option_name)
        if value is not None and value != '':
            return value
        return get_string_or_default('DEFAULT', option_name, default_value)
    return default_value


def is_debugging_enabled(section: str) -> bool:
    """
    Determines if debuggins is enabled for a given section (usually related to a plugin)
    """
    return get_boolean_or_default(section, 'debug', False)


def get_plugin_logger(plugin_name: str) -> logging.Logger:
    """
    Gets a logger for the supplied plugin
    """
    logger = logging.getLogger(f'{plugin_name}-plugin')
    logger.setLevel(logging.DEBUG if is_debugging_enabled(plugin_name) else logging.INFO)
    return logger
