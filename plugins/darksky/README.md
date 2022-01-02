# [Dark Sky](http://darksky.net) Plugin

Reads the outside temperature at your EvoHome location.

## Prerequisites
* A Dark Sky developer API key, available from [here](http://darksky.net/dev/)
* The Forecast python client installed on the same machine:

  `pip install python-forecastio`

  or, to upgrade your existing one:
  
  `pip install python-forecastio --upgrade`

## config.ini settings
```
[DarkSky]
apiKey=<your forecast.io api key>
latitude=<latitude of the location you want to monitor>
longitude=<longitude of the location you want to monitor>
Outside=<name you want to call this "zone" - default "Outside"> - recommend this setting is in the DEFAULT section of config.ini for all plugins to use
```

## Changelog
### 2.0.0 (2021-12-28)
- Upgraded to Python 3.9
- Additional logging and bug fixes
### 1.0.0 (2017)
Initial release


[Powered by Dark Sky](https://darksky.net/poweredby/)
