"""
Plugin module loader
"""
# pylint: disable=R0903

import imp # pylint: disable=deprecated-module
import os
import logging

from AppConfig import AppConfig


class PluginLoader:
    """
    Plugin Loader to load configured plugins from the plugins folder
    """

    __MAIN_MODULE ='__init__' # The main module name to look for in the plugin folder

    def __init__(self, config: AppConfig, allowed_plugins, plugins_folder: str):
        self.__logger = logging.getLogger('pluginloader')
        self.__logger.debug("Loading Plugins from %s....", plugins_folder)
        self.__config = config
        self.inputs = []
        self.outputs = []
        possibleplugins = os.listdir(plugins_folder)
        allowed_plugins_dict = {}

        for item in allowed_plugins:
            allowed_plugins_dict[item.lower()] = item

        for plugin in possibleplugins:
            location = os.path.join(plugins_folder, plugin)
            if not os.path.isdir(location) or not PluginLoader.__MAIN_MODULE + ".py" in os.listdir(location):
                continue
            self.__logger.debug("Plugin: %s", plugin)
            if (len(list(allowed_plugins)) == 0) or (plugin.lower() in allowed_plugins_dict):
                section_name = allowed_plugins_dict[plugin.lower()]
                disabled = config.get_boolean_or_default(section_name, 'disabled', False)
                if disabled:
                    self.__logger.debug("%s specifically disabled in config", section_name)
                    continue
                info = imp.find_module(PluginLoader.__MAIN_MODULE, [location])
                plugin_module = imp.load_module(PluginLoader.__MAIN_MODULE, *info)
                self.__logger.info("Plugin: %s loaded", section_name)
                if plugin_module.Plugin(self.__config).plugin_type=="output":
                    self.outputs.append({"name": plugin, "info": info})
                else:
                    self.inputs.append({"name": plugin, "info": info})
            else:
                self.__logger.debug("%s disabled - not in allowed list", plugin)


    def load(self, plugin: str):
        """
        Loads and returns a plugin module
        """
        self.__logger.debug("load(%s)", plugin['name'])
        return imp.load_module(PluginLoader.__MAIN_MODULE, *plugin["info"]).Plugin(self.__config)
