import plotly
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *
from collections import OrderedDict
import logging
import ConfigParser

plugin_name = "Plot.ly"
plugin_type="output"

plotly_logger = logging.getLogger('plotly-plugin:')

invalidConfig = False

try:
    config = configparser.SafeConfigParser(allow_no_value=True)
    config.read('config.ini')

    plotly_username = config.get("Plotly", "username")
    plotly_api_key = config.get("Plotly", "apiKey")
    if config.has_option('Plotly', 'maxPointsPerGraph'):
        ploty_max_points_per_graph = config.getint('Plotly', 'maxPointsPerGraph')
    else:
        ploty_max_points_per_graph = 288

except Exception as e:
    plotly_logger.error("Error reading config:\n%s", e)
    invalidConfig = True


def get_zones():
    zones = {}
    for key, zone in config.items('Plotly.Rooms'):
        if not key.lower() in defaults:
            zones[zone] = key
    zones = OrderedDict(sorted(zones.items(), key=lambda x: x[1]))
    return zones


defaults = map(lambda d: d.lower(), config.defaults().keys())

stream_ids_array = []
zones = get_zones()
for zone in zones:
    stream_ids_array.append(zones[zone])


def create_plots():
    # We make a plot for every room
    plotly_logger.info('max points per graph: %s', ploty_max_points_per_graph)
    for zone in zones:
        plotly_logger.info('Creating graph for: %s' % zone)
        stream_id = zones[zone]
        stream = Stream(
            token=stream_id,
            maxpoints=ploty_max_points_per_graph
        )
        trace1 = Scatter(
            x=[],
            y=[],
            mode='lines+markers',
            line=Line(
                shape='spline'
            ),
            stream=stream
        )

        data = Data([trace1])
        layout = Layout(title=zone)
        fig = Figure(data=data, layout=layout)
        py.plot(fig, filename=zone, fileopt='extend')


# if called directly then this is what will execute
# It will create the initial plot.ly reports if need be.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    plotly_logger.info('Creating Plot.ly graphs...')
    # we need to get the case-sensitive zone names (to match the EvoHome zone names)
    zoneReader = ConfigParser.ConfigParser(allow_no_value=True)
    zoneReader.optionxform = str
    zoneReader.read('config.ini')

    py.sign_in(plotly_username, plotly_api_key)

    tls.set_credentials_file(stream_ids=stream_ids_array)
    create_plots()
    exit(0)


from config_helper import *
plotly_debugEnabled = is_debugging_enabled('Plotly')
plotly_writeEnabled = not get_boolean_or_default('Plotly', 'Simulation', False)


def write(timestamp, temperatures):

    if invalidConfig:
        if plotly_debugEnabled:
            plotly_logger.debug('Invalid config, aborting write')
            return []

    debug_message = 'Writing to ' + plugin_name
    if not plotly_writeEnabled:
        debug_message += ' [SIMULATED]'
    plotly_logger.debug(debug_message)

    debug_text = '%s: ' % timestamp

    if plotly_writeEnabled:
        # Stream tokens from plotly
        tls.set_credentials_file(stream_ids=stream_ids_array)

    try:
        if plotly_writeEnabled:
            py.sign_in(plotly_username, plotly_api_key)

        for temperature in temperatures:
            debug_text += "%s (%s A" % (temperature.zone, temperature.actual)
            if temperature.target is not None:
                debug_text += ", %s T" % temperature.target
            debug_text += ') '

            if plotly_writeEnabled:
                if temperature.zone in zones:
                    stream_id = zones[temperature.zone]
                    s = py.Stream(stream_id)
                    s.open()
                    ts = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    s.write(dict(x=ts, y=temperature.actual))
                    s.close()
                else:
                    plotly_logger.debug("Zone %s does not have a stream id, ignoring")

    except Exception as e:
        plotly_logger.error("Plot.ly API error - aborting write\n%s", e)

    if plotly_debugEnabled:
        plotly_logger.debug(debug_text)
