"""
Plot.ly output plugin
** NOT WORKING AT THIS TIME **
"""
# pylint: disable=C0103,C0301,W0703

from collections import OrderedDict
from configparser import ConfigParser
import logging
import os
from pathlib import Path
import sys
#import plotly
import chart_studio
import chart_studio.plotly as py
#import chart_studio.tools as tls
import plotly.graph_objs as go
from config_helper import *

directory = Path(os.path.abspath(__file__))
sys.path.append(str(directory.parent.parent.parent))

plugin_name = "Plotly"
plugin_type="output"

__logger = get_plugin_logger(plugin_name)
__invalid_config = False

try:
    __simulation = get_boolean_or_default(plugin_name, 'Simulation', False)
    __config = get_config()
    __section = __config[plugin_name]
    plotly_username = __section['username']
    plotly_api_key = __section['apiKey']
    if __config.has_option(plugin_name, 'maxPointsPerGraph'):
        ploty_max_points_per_graph = __config.getint(plugin_name, 'maxPointsPerGraph')
    else:
        ploty_max_points_per_graph = 288

except Exception as config_ex:
    __logger.exception(f'Error reading config:\n{config_ex}')
    __invalid_config = True


def __get_zones():
    room_zones = {}
    for key, room in __config.items('Plotly.Rooms'):
        if not key.lower() in defaults:
            room_zones[room] = key
    room_zones = OrderedDict(sorted(room_zones.items(), key=lambda x: x[1]))
    return room_zones


defaults = map(lambda d: d.lower(), __config.defaults().keys())

stream_ids_array = []
zones = __get_zones()
for z in zones:
    stream_ids_array.append(zones[z])


def __create_plots():
    """
    Creates a plot for every room
    """
    __logger.debug(f'Max points per graph: {ploty_max_points_per_graph}')
    for zone in zones:
        __logger.debug(f'Creating graph for Zone: {zone}')
        stream_id = zones[zone]
        stream = go.Stream(
            token=stream_id,
            maxpoints=ploty_max_points_per_graph
        )
        trace1 = go.Scatter(
            x=[],
            y=[],
            mode='lines+markers',
            line=go.scatter.marker.Line(
                shape='spline'
            ),
            stream=stream
        )

        data = go.Data([trace1])
        layout = go.Layout(title=zone)
        fig = go.Figure(data=data, layout=layout)
        py.plot(fig, filename=zone, fileopt='extend')


def write(timestamp, temperatures):
    """
    Writes the temperatures to Plot.ly
    """

    if __invalid_config:
        __logger.debug('Invalid config, aborting write')
        return

    debug_message = 'Writing to ' + plugin_name
    if __simulation:
        debug_message += ' [SIMULATED]'
    __logger.debug(debug_message)

    debug_text = f'{timestamp}: '

  #  if plotly_writeEnabled:
        # Stream tokens from plotly
       # chart_studio.tools.set_credentials_file(username=plotly_username, api_key=plotly_api_key, stream_ids=stream_ids_array)

        #tls.set_credentials_file(stream_ids=stream_ids_array)

    try:
        if not __simulation:
            # Stream tokens from plotly
            chart_studio.tools.set_credentials_file(username=plotly_username, api_key=plotly_api_key, stream_ids=stream_ids_array)
        #    py.sign_in(plotly_username, plotly_api_key)

        for temperature in temperatures:
            debug_text += f'{temperature.zone} ({temperature.actual} A'
            if temperature.target is not None:
                debug_text += f', {temperature.target} T'
            debug_text += ') '

            if not __simulation:
                if temperature.zone in zones:
                    stream_id = zones[temperature.zone]
                    __logger.debug(f'Opening stream id: "{stream_id}" for zone: "{temperature.zone}"')
                    s = py.Stream(stream_id)
                    s.open()
                    ts = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    s.write(dict(x=ts, y=temperature.actual))
                    s.close()
                else:
                    __logger.debug(f'Zone "{temperature.zone}" does not have a stream id, ignoring')

    except Exception as e:
        __logger.exception(f'Plot.ly API error - aborting write\n{e}')

    if __simulation:
        __logger.info("[SIMULATED] %s", debug_text)
    else:
        __logger.debug(debug_text)




# if called directly then this is what will execute
# It will create the initial plot.ly reports if need be.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    __logger.debug('Creating Plot.ly graphs...')
    # we need to get the case-sensitive zone names (to match the EvoHome zone names)
    zoneReader = ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
    zoneReader.optionxform = str
    zoneReader.read('config.ini')

#    py.sign_in(plotly_username, plotly_api_key)

    chart_studio.tools.set_credentials_file(username=plotly_username, api_key=plotly_api_key, stream_ids=stream_ids_array)
  #  tls.set_credentials_file(stream_ids=stream_ids_array)
    __create_plots()
