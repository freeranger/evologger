"""
InfluxDB v1.x input plugin
"""

import urllib.parse
from influxdb import InfluxDBClient

from AppConfig import AppConfig
from plugins.PluginBase import OutputPluginBase

def _get_zone_measurements(time, zone, actual, target, logger):
    """
    Returns the actual, target, and delta data points for a zone
    """

    record_actual = None
    record_target = None
    record_delta = None

    def create_point(name: str, value: float):
        try:
            return {
                    "measurement": name,
                    "tags": {
                        "zone": zone,
                    },
                    "time": time,
                    "fields": {
                        "value": value
                    }
                }
        except Exception as e:
            logger.exception(f'Error creating data point for {name}, zone: {zone}, value: {value}:\n{e}')
            return {}

    if actual is not None and actual != '':
        record_actual = create_point("zone_temp.actual", float(actual))

    if target is not None and target != '':
        record_target = create_point("zone_temp.target", float(target))

    if record_actual is not None and record_target is not None:
        record_delta = create_point("zone_temp.delta", float(actual) - float(target))

    return record_actual, record_target, record_delta


class Plugin(OutputPluginBase):
    """InfluxDB v1.x output Plugin immplementation"""

    def _read_configuration(self, config: AppConfig):
        section = config[self.plugin_name]
        self._hostname = section["hostname"]
        self._port = section["port"]
        self._database = section["database"]
        self._username = section["username"]
        self._password = section["password"]
        self._logger.debug(f'Influx Host: {self._hostname}:{self._port} Database: {self._database}')

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'InfluxDB', 'output')

    def _write_temperatures(self, timestamp, temperatures):
        """
        Writes the temperatures to the database
        """

        influx_client = InfluxDBClient(self._hostname, self._port, self._username, self._password, self._database)

        data = []
        for temperature in temperatures:

            record_actual, record_target, record_delta = _get_zone_measurements(timestamp, temperature.zone, temperature.actual, temperature.target, self._logger)

            if record_actual:
                data.append(record_actual)
            if record_target:
                data.append(record_target)
            if record_delta:
                data.append(record_delta)

        try:
            if self._simulation is False:
                self._logger.debug('Writing all zone measurements to influx...')
                influx_client.write_points(data)
        except Exception as e:
            if hasattr(e, 'request'):
                self._logger.exception(f'Error Writing to {self._database} at {self._hostname}:{self._port} - aborting write.\nRequest: {e.request.method} {urllib.parse.unquote(e.request.url)}\nBody: {e.request.body}.\nResponse: {e.response}\nError:{e}')
            else:
                self._logger.exception(f'Error Writing to {self._database} at {self._hostname}:{self._port} - aborting write\nError:{e}')
