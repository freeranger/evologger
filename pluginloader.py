import imp
import os
import logging
import ConfigParser
from config_helper import get_boolean_or_default

plugin_logger = logging.getLogger('pluginloader::')


class PluginLoader:

    def __init__(self, allowed_plugins=[]):

        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read('config.ini')

        self.plugins_folder = './plugins'   # Location of the plugins
        self.mainModule = '__init__'        #The main module name to look for in the plugin folder

        plugin_logger.debug("Loading Plugins from %s....", self.plugins_folder)

        self.inputs = []
        self.outputs = []
        possibleplugins = os.listdir(self.plugins_folder)
        allowedPluginsDict = {}

        for item in allowed_plugins:
            allowedPluginsDict[item.lower()] = item

        for plugin in possibleplugins:
            location = os.path.join(self.plugins_folder, plugin)
            if not os.path.isdir(location) or not self.mainModule + ".py" in os.listdir(location):
                continue
            plugin_logger.debug('Plugin: %s', plugin)
            if (len(allowed_plugins) == 0) or (allowedPluginsDict.has_key(plugin.lower())):
                section_name = allowedPluginsDict[plugin.lower()]
                disabled = get_boolean_or_default(section_name, 'disabled', False)
                if disabled:
                    plugin_logger.debug('%s specifically disabled in config', section_name)
                    continue
                info = imp.find_module(self.mainModule, [location])
                p = imp.load_module(self.mainModule, *info)
                plugin_logger.info('%s loaded', section_name)
                if p.plugin_type=="output":
                    self.outputs.append({"name": plugin, "info": info})
                else:
                    self.inputs.append({"name": plugin, "info": info})
            else:
                plugin_logger.debug('%s disabled - not in allowed list', plugin)

    def get(self, plugin):
        plugin_logger.debug('get(%s)', plugin["name"])
        return imp.load_module(self.mainModule, *plugin["info"])

