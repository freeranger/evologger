# Evo Logger

## Purpose

To allow you to read your actual and desired temperatures from your [EvoHome](http://www.honeywelluk.com/products/Systems/Zoned/evohome-Main/) system (and others) and log them to a variety of destinations.

Destinations include "data stores" such as .csv files or influxdb database for further ingestion by Excel or [grafana](https://grafana.net) respectively, or directly to graphing websites such as [Plot.ly](http://plot.ly.com) and [emoncms](https://emoncms.org)

## Getting Started
1. Clone the entire repo to your preferred location.
2. Configure the global settings in the `[DEFAULT]` section of `config.ini` 
3. Configure each plugin in `config.ini` according to your needs - see the `README.md` file with each plugin for details on how to configure it.
   All plugins live in the "plugins" folder - you can delete ones you don't want (and remove the relevant `config.ini` section) or add `disabled` to the relevant `config.ini` section to explicitly disable it
4. run it!  
   - Locally
      - `pip3 install -r requirements.txt` to add the required python packages (for all plugins)   
      - `python3 evologger.py` to start the application (add -h for help)
   - In Docker
      - See below to run in Docker

## Running in Docker
A `Dockerfile` is included so you can run evologger in a Docker container if you wish.
From the source folder:
1. `docker build -t evologger .`
2. Run:
   - `docker run --rm -it evologger` (to run in the foregound with coloured output)
   -  `docker run --rm -d evologger` (to run in detached mode)

It is beyond the scope of this document to describe how to use docker but you could map the `config.ini` file into the container so you just need to restart with a new config, and you can map a volume/file for csv output rather than storing in the container volume.

**Note** If you are running services in other containers on the same host that you wish to accerss (e.g. Influx) then you need to use `host.docker.internal` in place of the host name or IP you would otherwise use - or you could use a docker compose file and ensure they are in the same docker network


## [DEFAULT] config.ini settings
```
[DEFAULT]
debug=<true|false>      - If true then output debugging statements.
pollingInterval=600     - Frequency in seconds to read temperatures from input plugins and write them to the output plugins.  0 => do once, then exit
                          It is recommended that this is set to no less than 5 minutes as some of the api's used by plugins (e.g. plot.ly) limit the numer of api calls you can make per day.
Outside=<zone name>     - Name you want to use for your outside "zone" (if you have one) when reading the external temperature - used by some input plugins, e.g. darksky.net, netatmo
HotWater=Hot Water      - Name you want to use for the Hot Water "zone" (if you have one) when reading the temperature - used by some plugins, e.g. evohome, console
```

## Plugins
Evologger supports a "plugin" architecture where you can add new input sources and output destinations simply by adding the plugin to the `plugins` directory and adding any necessary configuration to the `config.ini` file.

Any plugins you don't want to use, it's probably best to remove their section(s) from the `config.ini` file completely.

### Available plugins
##### Inputs
* [Evohome](https://github.com/freeranger/evologger/blob/master/plugins/evohome/readme.md) - essential to collect values from your EvoHome system (via the [evohome-client](https://github.com/watchforstock/evohome-client) library)
* [Darksky](https://github.com/freeranger/evologger/blob/master/plugins/darksky/readme.md) - Reads the current local temperature from [darksky.net](http://darksky.net) at the same time as your room temps are read
* [Netatmo Weather station](https://www.netatmo.com/en-gb/weather) - reads the temperature from your weather station's Outdoor module at the same time as your room temps are read

##### Outputs
* [Console](https://github.com/freeranger/evologger/blob/master/plugins/console/readme.md) - writes to the console
* [Csv](https://github.com/freeranger/evologger/blob/master/plugins/csv/readme.md) - write to a csv file so you can generate your own graphs or whatever in Excel
* [InfluxDb 1.x](https://github.com/freeranger/evologger/blob/master/plugins/influxdb/readme.md) - write to an InfluxDB 1.x timeseries database so you can then graph in [grafana](https://grafana.net) for example.
* [InfluxDb 2.x](https://github.com/freeranger/evologger/blob/master/plugins/influxdb2/readme.md) - write to an InfluxDB 2.x timeseries database so you can then graph in [grafana](https://grafana.net) for example.
* [Plot.ly](https://github.com/freeranger/evologger/blob/master/plugins/plotly/readme.md) - write directly to [Plot.ly](http://plot.ly.com) streams for live updating graphs
* [Emoncms](https://github.com/freeranger/evologger/blob/master/plugins/emoncms/readme.md) - write directly to [emoncms](https://emoncms.org) inputs

See the readme file in each plugin's folder for instructions on any specific configuration or initialisation steps required.

All plugins support the following options in `config.ini`:

```
disabled=<true|false>   - If true then the plugin is disabled completely and will never be invoked
simulation=<true|false> - if true then input plugins will return random values rather than contacting the 
                          source whilst output plugins will write to the debug log but not the actual 
                          destination.  Default: false if not present
debug=<true|false>      - If true then write to the debug log.  If not present then follows the debug setting
                          in the [DEFAULT] section of the config file.  If present and false (the only time it
                          makes sense to add this value) then do not write debug output for this specific plugin only
                          even if the [DEFAULT] setting is to debug
```

#### Creating your own plugins
Plugins come in two flavours - input plugins and output plugins. 
Input plugins are sources of temperature data and output plugins are where you record that data.

The simplest way to get started with your own plugin is to look at one of the existing ones - eg. darksky.net for input or csv for output.

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
* Only a single EvoHome location is currently supported (you can specify which one if you have multiple locations)
* In theory this should work as a scheduled job (cron|launchd|whatever windows uses) but I have no idea how to get the scheduled "environment" to pick up the same python 
  settings/config as a conole app for a logged on user picks up (various attempts failed) so I just run it in a console window and leave it open.
  
  
## Changelog
### 2.1.0 (2021-01-82)
- Netatmo plugin added (v 1.0.0)
- Fix changelog dates 
- get_string_or_default will select from the DEFAULT section if an empty key exists in the plugin section
- read_temperatures sorts the temps using the actual configured OutsideZone name and not hard coded 'Outside'
- Evohome plugin updated (v 2.0.1)

### 2.0.0 (2021-12-28)
- Upgraded to Python 3.9
- Additional logging and bug fixes
- New output plugins
  - Console
  - InfluxDB 2.x
- Note: The following do not work at the moment and will hopefully be addressed soon
  - The Plot.ly plugin
  - Unit tests

### 1.0.0 (2017)
Initial release


---
**Disclaimer**  
I am not a Python programmer - this is probably awful python code, but it works for me - use at your own risk.  
