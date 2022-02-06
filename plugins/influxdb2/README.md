# [InfluxDB 2.x](https://influxdata.com/time-series-platform/influxdb/) Plugin

Writes the temperatures to an [InfluxDB 2.x](https://www.influxdata.com) bucket (database).

## Prerequisites
* An InfluxDB 2.x instance you can access
* An InfluxDB organisation containing
* An InfluxDB bucket to store the temperature data in
* An InfluxDB API Key with write access to same
* The Influx python client installed on the same machine:

  `pip install influxdb-client`

  or, to upgrade your existing one:

  `pip install influxdb-client --upgrade`

## config.ini settings
```
[InfluxDB]
hostname=<hostname or IP of the InfluxDB host>
port=<Port for the influx db - usually 8086>
org=<Organisation to use>
bucket=<Bucket to store the data in>
apikey=<API key with write access to the bucket>
```

## [Grafana](https://grafana.net)
[Grafana](https://grafana.net) is a visualisation tool which can read data from an Influx database (others are available)
The installation process for [Grafana](https://grafana.net) is described here [here](http://docs.grafana.org/installation/).
Once you have installed [Grafana](https://grafana.net) you can create a dashboard to show all your evohome temperatures, e.g.

1. Add your influx database to grafana: http://docs.grafana.org/datasources/influxdb/
   Note: This has only been tested in v2 with Flux query language selected
2. Create or edit a dashboard
3. Add a graph per zone and:
    1. Select your InfluxDB as the "panel data source"
    2. Add the Actual temperature, e.g.:
        * For InfluxQL sources (assuming nothing has changed from InfluxDB v1)
          1. From: default zone_temp.actual
          2. Where: zone = Kitchen
          3. Select: field(value)
          4. Group By: tag(zone)
          5. Format as: Timeseries.
        * For Flux sources (InfluxDB v2) you write a query, e.g.
```
            from(bucket: "evohome")
              |> range(start: v.timeRangeStart, stop:v.timeRangeStop)
              |> filter(fn: (r) =>
                r._measurement == "zone_temp.actual" and
                r._field == "value"
              )
```

Repeat Step 3 for the expected temperature specifying zone_temp.target instead of zone_temp.actual

Repeat Step 3.2 For each zone you want on the graph if using an InfluxQL source.

## Changelog
### 2.0.0 (2022-02-06)
- Rewritten to use the new plugin model
### 1.0.0 (2021-12-28)
Initial release
