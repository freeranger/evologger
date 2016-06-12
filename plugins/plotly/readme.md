# [Plot.ly](https://plot.ly) Plugin

Writes the temperatures to a set of [Plot.ly](https://plot.ly) streams.

## Prerequisites
* Your username from your [Plot.ly](https://plot.ly)account
* A Plot.ly API key, available from [here](https://plot.ly/settings/api)
* One streaming API token per zone you want to graph, available from [here](https://plot.ly/settings/api)
* The Plot.ly python client should be installed on the same machine:  
  `pip install plotly`

## config.ini settings
```
[Plotly]
username=<Plot.ly username>
apiKey=<Plot.ly API key>
maxPointsPerGraph=<maximum number of points to store per graph>. This is optional, defaulting to 288.
```

You also need an additional section in `config.ini` containing the list of zones as per the Evohome system, plus the "Outside" and "Hot Water" zone names if you are logging this data also.
**Note:** The latter two must exactly match the names you placed in the `[DEFAULT]` section of `config.ini` for `HotWater=` and `Outside=` respectively.
```
[Plotly.Rooms]
<streamid>=<zonename> pairs to map plot.ly stream id's to evohome zone names.
e.g.
123ivgtpwn=Kitchen
945ivfrrbf=Office
etc...
```

## Setup ##
Once you have added the username, API Key, and streaming API tokens to your config.ini, you need to initialise the streams for the first time.
From the evohome-logger folder, run:
```
python plugins/plotly/__init__.py
```

You will need to repeat this if you add more zones or change stream id's etc