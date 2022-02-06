# [InfluxDB 1.x](https://influxdata.com/time-series-platform/influxdb/) Plugin

Writes the temperatures to an [InfluxDB 1.x](https://www.influxdata.com) database.

## Prerequisites
* An InfluxDB 1.x instance you can access
* An Influx database to store the temperature data in
* An Influx username, and password with write access to same
* The Influx python client installed on the same machine:

  `pip install influxdb`

  or, to upgrade your existing one:

  `pip install influxdb --upgrade`

## config.ini settings
```
[InfluxDB]
hostname=<hostname or IP of the InfluxDB host>
port=<Port for the influx db - usually 8086>
database=<Database to store the data in>
username=<User with access to the database>
password=<Password for the user>
```

## [Grafana](https://grafana.net)
[Grafana](https://grafana.net) is a visualisation tool which can read data from an Influx database (others are available)
The installation process for [Grafana](https://grafana.net) is described here [here](http://docs.grafana.org/installation/).
Once you have installed [Grafana](https://grafana.net) you can create a dashboard to show all your evohome temperatures, e.g.

1. Add your influx database to grafana: http://docs.grafana.org/datasources/influxdb/
2. Create or edit a dashboard
3. Add a graph per zone and:
    1. Select your InfluxDB as the "panel data source"
    2. Add the Actual temperature, e.g.:
    3. From: default zone_temp.actual
    4. Where: zone = Kitchen
    5. Select: field(value)
    6. Group By: tag(zone)
    7. Format as: Timeseries.
    8. Repeat for the expected temperature selecting, zone_temp.target instead of zone_temp.actual


## Changelog
### 3.0.0 (2022-02-06)
- Rewritten to use the new plugin model
### 2.0.0 (2021-12-28)
- Upgraded to Python 3.9
- Additional logging and bug fixes
### 1.0.0 (2017)
Initial release

