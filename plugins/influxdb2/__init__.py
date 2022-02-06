"""
InfluxDB v2.x input plugin
"""

import sys
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

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
            return Point(name).time(time).tag("zone", zone).field("value", value)
        except Exception as e:
            logger.exception(f'Error creating data point for {name}, zone: {zone}, value: {value}:\n{e}')
            return Point(name)

    if actual is not None and actual != '':
        record_actual = create_point("zone_temp.actual", float(actual))

    if target is not None and target != '':
        record_target = create_point("zone_temp.target", float(target))

    if record_actual is not None and record_target is not None:
        record_delta = create_point("zone_temp.delta", float(actual) - float(target))

    return record_actual, record_target, record_delta


class Plugin(OutputPluginBase):
    """InfluxDB v2.x output Plugin immplementation"""

    def _read_configuration(self, config: AppConfig):
        section = config[self.plugin_name]
        self._hostname = section["hostname"]
        self._port = section["port"]
        self._org = section["org"]
        self._bucket = section["bucket"]
        self._apikey = section["apikey"]
        self._logger.debug(f'Influx Host: {self._hostname}:{self._port} Org: {self._org}, Bucket:{self._bucket}')


    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'InfluxDB2', 'output')

    def _write_temperatures(self, timestamp, temperatures):
        """
        Writes the temperatures to the org bucket
        """

        influx_client = InfluxDBClient(url=f'{self._hostname}:{self._port}', token=self._apikey, org=self._org)
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)

        text_temperatures = ''
        data = []
        for temperature in temperatures:

            record_actual, record_target, record_delta = _get_zone_measurements(timestamp, temperature.zone, temperature.actual, temperature.target, self._logger)

            if record_actual:
                data.append(record_actual)
            if record_target:
                data.append(record_target)
            if record_delta:
                data.append(record_delta)

            text_temperatures += f'{temperature.zone} ({temperature.actual} A'
            if temperature.target is not None:
                text_temperatures += f', {temperature.target} T'
            text_temperatures += ') '

        try:
            if self._simulation is False:
                self._logger.debug(text_temperatures)
                self._logger.debug('Writing all zone measurements to influx...')
                write_api.write(bucket=self._bucket, record=data)
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status == 401:
                    self._logger.exception(f'Insufficient write permissions to Bucket: "{self._bucket}" - aborting write\nError:{e}')
                else:
                    self._logger.exception(f'Error Writing to {self._bucket} at {self._hostname}:{self._port} - aborting write.\nResponse: {e.body.json()}\nError:{e}')
                return text_temperatures
            self._logger.exception(f'Error Writing to {self._bucket} at {self._hostname}:{self._port} - aborting write\nError:{e}')

        return text_temperatures
