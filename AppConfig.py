"""
Helpers for configuring the app/plugins
"""

from configparser import ConfigParser


class AppConfig(ConfigParser):
    """Application Configuration"""

    def __init__(self, config_file) -> None:
        super().__init__(allow_no_value=True, inline_comment_prefixes=";")
        self.read(config_file)

    def get_boolean_or_default(self, section_name: str, option_name: str, default_value: bool) -> bool:
        """Gets a boolean value from config or returns the default value if not found

        Args:
            section_name (str): The section name
            option_name (str): The option name (key) in the section
            default_value (bool): The default value to return if the config value does not exist

        Returns:
            bool: The boolean value of the supplied option or the default value if it does not exist
        """

        if self.has_option(section_name, option_name):
            value = self.get(section_name, option_name)

            return True if value is None else value.lower() == 'true'
        return default_value


    def get_float_or_default(self, section_name: str, option_name: str, default_value: float) -> float:
        """Gets a float value from config or returns the default value if not found

        Args:
            section_name (str): The section name
            option_name (str): The option name (key) in the section
            default_value (float): The default value to return if the config value does not exist

        Returns:
            bool: The flot value of the supplied option or the default value if it does not exist
        """

        if self.has_option(section_name, option_name):
            value = self.getfloat(section_name, option_name)
            return value
        return default_value


    def get_string_or_default(self, section_name: str, option_name: str, default_value: str) -> str:
        """Gets a string value from config or returns the default value if not found

        Args:
            section_name (str): The section name
            option_name (str): The option name (key) in the section
            default_value (str): The default value to return if the config vlaue does not exist

        Returns:
            str: The string value of the supplied option or the default value if it does not exist
        """

        if self.has_option(section_name, option_name):
            value = self.get(section_name, option_name)
            if value is not None and value != '':
                return value
            return self.get_string_or_default('DEFAULT', option_name, default_value)
        return default_value


    def is_debugging_enabled(self, section: str) -> bool:
        """
        Determines if debuggins is enabled for a given section (usually related to a plugin)
        """
        return self.get_boolean_or_default(section, 'debug', False)
