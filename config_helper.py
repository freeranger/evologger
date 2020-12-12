import configparser
import logging
config_logger = logging.getLogger(__name__)

config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')


def get_boolean_or_default(section_name, option_name, default_value):
    # config_logger.debug('get_boolean_or_default(%s, %s, %s)', sectionName, optionName, defaultValue)
    if config.has_option(section_name, option_name):
        value = config.get(section_name, option_name)

        if value is None:
            return True
        else:
            if value.lower() == 'true': 
                return True 
            else: 
                return False
    else:
        return default_value

def get_string_or_default(section_name, option_name, default_value):
    if config.has_option(section_name, option_name):
        value = config.get(section_name, option_name)
        return value
    else:
        return default_value


def is_debugging_enabled(section):
    return get_boolean_or_default(section, 'debug', False)
