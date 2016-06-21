# [Emoncms](https://emoncms.org) Plugin

Writes the temperatures to [Emoncms](https://emoncms.org).

## Prerequisites
* An [Emoncms](https://emoncms.org) Read & Write API key, available from [here](https://emoncms.org/site/api#input) once you have signed up with them
* A node number to use - basically just decide which node will receive the evologger data - no actual configuration required at this stage.

## config.ini settings
```
[Emoncms]
apiKey=<your emoncms read/write  api key>
nodeNumber=<the node number to use?
```

## Setting up Emoncms *
Once you have configured the plugin and run evologger to log at least one set of temperatures into emon, you can configure the feeds and inputs so you can create visualisations of your data as follows:

1. Log into [Emoncms](https://emoncms.org)
2. Navigate to the [Inputs](https://emoncms.org/input/view) page (follow the link or find it on the "setup" menu)
   Here you will see all your current actual and target temperatures, one per zone, named <zonename>Actual or <zonename>Target as appropriate
3. For each entry, click on the "spanner" icon on the right to add a process, with the following values:
    * Process: Log to feed
    * Create New
    * Set a name for the node if you don't like the default
    * Feed Engine: Fixed Interval (PHPFINA)
    * Time: Set this to the same interval as the polling interval in `config.ini`, remembering that it is in seconds in - eg. `config.ini` would be 5 minutes here
4. Go to the [Feeds](https://emoncms.org/feed) page (follow the link or find it on the "setup" menu)
5. All you current actual and target temperature feeds will be in one table. You can edit each line and add a Tag and rename the display name by using the pencil icon. You might, for example, tag all the radiator zones as "Heating".  
   This step is optional.
   
At this point emoncms is now logging all your data and you can start to create graphs.  
The easiest way to see a graph is to click on one of the eye icons next to a value you want to see on the  [Feeds](https://emoncms.org/feed) page.
You can add or remove other feeds to e.g. compare target vs actual temp, compare different rooms etc.

You can now create dashboards to create more permanent graphs and do other visualisations such as using gauges to show current temps.

_<sub>* Thanks to bmccluskey from the automatedhome.co.uk for these excellent instructions.</sub>_