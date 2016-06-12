# EvoHome Plugin

Reads the temperatures from your [EvoHome](http://www.honeywelluk.com/products/Systems/Zoned/evohome-Main/) system.

## Prerequisites
* An EvoHome system :)
* Your EvoHome username and password - the ones used to log into https://www.mytotalconnectcomfort.com/
* The EvoHome python client installed on the same machine you are running this plugin from: https://github.com/watchforstock/evohome-client 
`  pip install evohomeclient`

## config.ini settings
```
[EvoHome]
username=<evohome username>
password=<evohome password>

Note: These two are only required if you have hot water control
HotWater=<name you want for the hot water "zone"> - recommend this is in the DEFAULT section of config.ini for all plugins to use
HotWaterSetPoint=<Target temperature for Hot Water when it is on>
```

## Limitations
* It is not possible to retrieve the desired hot water temp from the evohome api, so you must supply the `HotWaterSetPoint` value in the `config.ini` file.
* We also don't know directly if the hot water is meant to be on or off at any given moment in time.
  With a little hackery-pokery however, the plugin can determine if the hot water is on or off, so OFF => desired temp = 0, ON => desired temp = HotWaterSetPoint.
* Only a single EvoHome location is supported.
