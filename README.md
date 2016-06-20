# Evo Logger

### Purpose

To allow you to read your actual and desired temperatures from your [EvoHome](http://www.honeywelluk.com/products/Systems/Zoned/evohome-Main/) system (and others) and log them to a variety of destinations.
Destinations include "data stores" such as .csv files or influxdb database for further injestion by Excel or [grafana](https://grafana.net) respectively, or directly to graphing websites such as [Plot.ly](http://plot.ly.com) and [emoncms](https://emoncms.org)

### Getting Started
1. Clone the entire repo to your preferred location.
2. Configure the global settings in the `[DEFAULT]` section of `config.ini` 
2. Configure each plugin in `config.ini` according to your needs - see the `readme.md` file with each plugin for details on how to configure it.
   All plugins live in the "plugins" folder - you can delete ones you don't want or add `disabled` to the relevant `config.ini` section to disable it
3. run it!  
   `python evologger.py`

   
#### [DEFAULT] config.ini settings
```
[DEFAULT]
debug=<true|false>      - If true then output debugging statements.
pollingInterval=300     - Frequency in seconds to read temperatures from input plugins and write them to the output plugins.  0 => do once, then exit
                          It is recommended that this is set to no less than 5 minutes as some of the api's used by plugins (e.g. plot.ly) limit the numer of api calls you can make per day.
Outside=<zone name>     - Name you want to use for your outside "zone" (if you have one) when reading the external temperature - used by some input plugins, e.g. forecast.io
HotWater=Hot Water      - Name you want to use for the Hot Water "zone" (if you have one) when reading the temperature - used by some input plugins, e.g. evohome
```

### Plugins
Evologger supports a "plugin" architecture where you can add new input sources and output destinations simply by adding the plugin to the `plugins` directory and adding any necessary configuration to the `config.ini` file.

#### Available plugins
#####Inputs
* [Evohome](https://github.com/freeranger/evologger/blob/master/plugins/evohome/readme.md) - essential to collect values from your EvoHome system (via the [evohome-client](https://github.com/watchforstock/evohome-client) library)
* [Forecast](https://github.com/freeranger/evologger/blob/master/plugins/forecast/readme.md) - Reads the current local temperature from [forecast.io](http://forecast.io/) at the same time as your room temps are read

#####Outputs
* [Csv](https://github.com/freeranger/evologger/blob/master/plugins/csv/readme.md) - write to a csv file so you can generate your own graphs or whatever in Excel
* [InfluxDb](https://github.com/freeranger/evologger/blob/master/plugins/influxdb/readme.md) - write to this timeseries database so you can then graph in [grafana](https://grafana.net) for example.
* [Plot.ly](https://github.com/freeranger/evologger/blob/master/plugins/plotly/readme.md) - write directly to [Plot.ly](http://plot.ly.com) streams for live updating graphs
* [Emoncms](https://github.com/freeranger/evologger/blob/master/plugins/emoncms/readme.md) - write directly to [emoncms](https://emoncms.org) inputs

See the readme file in each plugin's folder for instructions on any specific configuration required.

All plugins support the following options in `config.ini`:

```
disabled=<true|false>   - If true then the plugin is disabled completely and will never be invoked
simulation=<true|false> - if true then input plugins will return random values rather than contacting the 
                          source and output plugins will write to the debug log but not the actual 
                          destination.  Default: false if not present
debug=<true|false>      - If true then write to the debug log.  If not present then follows the debug setting
                          in the [DEFAULT] section of the config file.  If present and false (the only time it
                          makes sense to add this value) then do not write debug output for this specific plugin only
                          even if the [DEFAULT] setting is to debug
```

####Creating your own plugins
Plugins come in two flavours - input plugins and output plugins. 
Input plugins are sources of temperature data and output plugins are where you record that data.

The simplest way to get started with your own plugin is to look at one of the existing ones - eg. forecast for input or csv for output.
There are a few rules you must follow for your plugin:

* Plugins must be stored beneath the "plugins" folder and have a `__init__.py` file.
* The name of the plugin folder should match the name of the section in the `config.ini`
* The plugin must contain two properties - `plugin_name` - the name of the plugin and `plugin_type` - `"input" or "output"`
* The plugin should support the `disabled|simulation|debug` options in `config.ini` as described previously
* An input plugin must have a method `read` which takes no parameters and returns an array of Temperature objects with these properties:
    * zone - the name of the "zone" the temperature is for
    * actual - the actual temperature
    * target - the target temperature - this is optional - do not supply if target has no meaning for this plugin (e.g. when reading outside temperature)
* An output plugin must have a method `write` which takes two parameters:
    * timestamp - the time in UTC when the temperature readings were taken
    * temperatures - an array of Temperature object, with the same format as emitted by the input plugins


## Limitations
* Only a single EvoHome location is currently supported
* In theory this should work as a scheduled job (cron|launchd|whatever windows uses) but I have no idea how to get the scheduled "environment" to pick up the same python 
  settings/config as a conole app for a logged on user picks up (various attempts failed) so I just run it in a console window and leave it open.
  
  
  
---
**Disclaimer**  
I am not a Python programmer - this is probably awful python code, but it works for me - use at your own risk.  
