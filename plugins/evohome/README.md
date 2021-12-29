# EvoHome Plugin

Reads the temperatures from your [EvoHome](http://www.honeywelluk.com/products/Systems/Zoned/evohome-Main/) system.

## Prerequisites
* An EvoHome system :)
* Your EvoHome username and password - the ones used to log into https://www.mytotalconnectcomfort.com/
* The EvoHome python client installed on the same machine you are running this plugin from:

  `pip install evohomeclient`

  or, to upgrade your existing one:
  
  `pip install evohomeclient --upgrade`

## config.ini settings
```
[EvoHome]
username=<evohome username>
password=<evohome password>
location=<location id or location name> 

Note: location is optional - only specify it if you have more than one location, or want to use anything other than the first location
You can specify the name of the location or the id.  The name is exactly as registered on the EvoHome/Totalconnect website.
If you want to specify the id because the location name is not unique, click on the location name in the EvoHome/Totalconnect website and the
url will change to something like https://international.mytotalconnectcomfort.com/Locations/View/12345 - 12345 is your location id

HotWater=<name you want for the hot water "zone"> - recommend this is actually placed in the DEFAULT section of config.ini for all plugins to use
HotWaterSetPoint=<Target temperature for Hot Water when it is on>
Note: These two are only required if you have hot water control
```
 
## Limitations
* It is not possible to retrieve the desired hot water temp from the evohome api, so you must supply the `HotWaterSetPoint` value in the `config.ini` file.
* We also don't know directly if the hot water is meant to be on or off at any given moment in time.
  With a little hackery-pokery however, the plugin can determine if the hot water is on or off, so OFF => desired temp = 0, ON => desired temp = HotWaterSetPoint.
* Only a single EvoHome location is supported (for reading temps from) though your installation may have multiple locations - use the "location" config setting to specify the one you wish to log.


## Changelog
### 2.0.0 (2022-12-28)
- Upgraded to Python 3.9
- Add support for cached access tokens
- Additional logging and bug fixes

### 1.0.0 (2017)
Initial release

[Powered by the EvoHome Client](https://github.com/watchforstock/evohome-client)

