# [Netatmo Weather station](https://www.netatmo.com/en-gb/weather) Plugin

Reads the outside temperature from your Netatmo outdoor module.

## Prerequisites
* A Netatmo weather station with indoor and outdoor modules
* Your Netatmo username and password - the ones used to log into https://my.netatmo.com/app/station
* A Netatmo app client id and secret, available from [here](https://dev.netatmo.com/apps/) - just create a new app to generate the values.

## config.ini settings
```
[Netatmo]
username=<netatmo username>
password=<netatmo username>
clientId=<netatmo app client id>
clientSecret=<netatmo app client secret>
StationName=optional, name of the (indoor) weather station to use if you have more than one/auto discovery fails - remove or leave blank to attempt auto discovery>
OutdoorModule=<optional, name of the outdoor module attached to the station to use if you have more than one/auto discovery fails - remove or leave blank to attempt auto discovery>
Outside=<name you want to call this "zone" - default "Outside"> - recommend this setting is in the DEFAULT section of config.ini for all plugins to use
```

## Notes
- Authentication Tokens are cached in a file in a temp directory to avoid hitting rate limits when accessing the API.

## Changelog
### 1.0.0 (2022-01-02)
Initial release

