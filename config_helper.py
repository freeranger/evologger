import ConfigParser
import logging
config_logger = logging.getLogger(__name__)

config = ConfigParser.ConfigParser(allow_no_value=True)
config.read('config.ini')


def get_boolean_or_default(section_name, option_name, default_value):
    # config_logger.debug('get_boolean_or_default(%s, %s, %s)', sectionName, optionName, defaultValue)
    if config.has_option(section_name, option_name):
        value = config.get(section_name, option_name)
        # config_logger.debug("%s: %s raw value: %s.", sectionName, optionName, value)

        if value is None:
            # config_logger.debug("%s: %s present but with no explict value, returning True.", sectionName, optionName)
            return True
        else:
            if value.lower() == 'true': 
                return True 
            else: 
                return False
    else:
        # config_logger.debug("%s: %s not found, returning default of %s.", sectionName, optionName, defaultValue)
        return default_value


def is_debugging_enabled(section):
    return get_boolean_or_default(section, 'debug', False)
