# [Forecast](http://forecast.io) Plugin

Reads the outside temperature at your EvoHome location.

## Prerequisites
* A Forecast developer API key, available from [here](https://developer.forecast.io)
* The Forecast python client installed on the same machine:
  `pip install python-forecastio`

## config.ini settings
```
[Forecast]
apiKey=<your forecast.io api key>
latitude=<latitude of the location you want to monitor>
longitude=<longitude of the location you want to monitor>
Outside=<name you want to call this "zone" - default "Outside"> recommend this setting is in the DEFAULT section of config.ini for all plugins to use
```