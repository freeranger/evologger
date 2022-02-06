"""
CSV file output plugin
"""
# pylint: disable=E1101,R1732,W0406

import csv
import os.path
from AppConfig import AppConfig
from plugins.PluginBase import OutputPluginBase

class Plugin(OutputPluginBase):
    """CSV output Plugin immplementation"""

    def _read_configuration(self, config: AppConfig):
        self._filename = config.get(self.plugin_name, "filename")

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config, 'Csv', 'output')

    def _write_temperatures(self, timestamp, temperatures):
        """
        Writes the temperatures to the configured file
        """

        csv_file = None
        writer = None

        csv_write_headers = not self._simulation and not os.path.isfile(self._filename)

        if not self._simulation:
            try:
                csv_file = open(self._filename, 'a', encoding='UTF-8')
            except Exception as e:
                self._logger.exception(f'Error opening {self._filename} for writing - aborting write\n{e}')
                return ''

            writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        if not self._simulation and csv_write_headers:

            self._logger.debug(f'Creating {self._filename}')

            fieldnames = ['Time']
            for t in temperatures:
                if t.target is not None:
                    fieldnames.append(t.zone + ' [A]')
                    fieldnames.append(t.zone + ' [T]')
                else:
                    fieldnames.append(t.zone)

            writer.writerow(fieldnames)

        text_temperatures = ''
        row = [timestamp]
        for temperature in temperatures:
            row.append(temperature.actual)
            text_temperatures += f'{temperature.zone} ({temperature.actual} A'

            if temperature.target is not None:
                row.append(temperature.target)
                text_temperatures += f', {temperature.target} T'
            text_temperatures += ') '

        if self._simulation is False:
            writer.writerow(row)
            csv_file.close()

        return text_temperatures
