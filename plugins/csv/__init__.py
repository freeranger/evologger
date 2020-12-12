import os.path
import csv
from config_helper import *

plugin_name = "CSV"
plugin_type = "output"

csv_logger = logging.getLogger('csv-plugin:')

invalidConfig = False

try:
    config = configparser.ConfigParser(allow_no_value=True)
    config.read('config.ini')

    filename = config.get("Csv", "filename")

    csv_debug_enabled = is_debugging_enabled('Csv')

    csv_write_enabled = not get_boolean_or_default('Csv', 'Simulation', False)

except Exception as e:
    csv_logger.error("Error reading config:\n%s", e)
    invalidConfig = True

def write(timestamp, temperatures):
    if invalidConfig:
        if csv_debug_enabled:
            csv_logger.debug('Invalid config, aborting write')
            return []

    debug_message = 'Writing to ' + plugin_name
    if not csv_write_enabled:
        debug_message += ' [SIMULATED]'
    csv_logger.debug(debug_message)

    csv_file = None
    writer = None

    csv_write_headers = csv_write_enabled and not os.path.isfile(filename)

    if csv_write_enabled:
        try:
            csv_file = open(filename, 'a')
        except Exception as e:
            csv_logger.error("Error opening %s for writing - aborting write\n%s", filename, e)
            return

        writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    if csv_write_enabled and csv_write_headers:

        if csv_debug_enabled:
            csv_logger.debug("Creating %s", filename)

        fieldnames = ['Time']
        for t in temperatures:
            if t.target is not None:
                fieldnames.append(t.zone + ' [A]')
                fieldnames.append(t.zone + ' [T]')
            else:
                fieldnames.append(t.zone)

        writer.writerow(fieldnames)

    debug_temperatures = '%s: ' % timestamp
    row = [timestamp]
    for temperature in temperatures:
        row.append(temperature.actual)
        debug_temperatures += "%s (%s A" % (temperature.zone, temperature.actual)

        if temperature.target is not None:
            row.append(temperature.target)
            debug_temperatures += ", %s T" % temperature.target
        debug_temperatures += ') '

    if csv_debug_enabled:
        csv_logger.debug(debug_temperatures)

    if csv_write_enabled:
        writer.writerow(row)

    if csv_write_enabled:
        csv_file.close()

# if called directly then this is what will execute
if __name__ == "__main__":
    import sys
    write(sys.argv[1], sys.argv[2])
