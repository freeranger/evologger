# [Emoncms](https://emoncms.org) Plugin

Writes the temperatures to [Emoncms](https://emoncms.org).

## Prerequisites
* An [Emoncms](https://emoncms.org) Read & Write API key, available from [here](https://emoncms.org/site/api#input) once you have signed up with them
* A node to use - basically just decide which node will receive the evologger data - no actual configuration required at this stage and the node does not need to exist in advance

## config.ini settings
```
[Emoncms]
apiKey=<your emoncms read/write  api key>
node=<the node to use>
```

## Setting up Emoncms *
Once you have configured the plugin and run evologger to log at least one set of temperatures into emon, you can configure the feeds and inputs so you can create visualisations of your data as follows:

1. Log into [Emoncms](https://emoncms.org)
2. Navigate to the [Inputs](https://emoncms.org/input/view) page (follow the link or find it on the "setup" menu)
   Here you will see all your current actual and target temperatures, one per zone, named <zonename>Actual or <zonename>Target as appropriate:
   ![inputs](https://cloud.githubusercontent.com/assets/1401069/16238545/c05da422-37d8-11e6-9d77-0a39cfffdd11.png)
3. For each entry, click on the "spanner" icon on the right to add a process, with the following values:
    ![addprocess](https://cloud.githubusercontent.com/assets/1401069/16238587/d7b2776a-37d8-11e6-8a2d-8b036a19e745.png)
    * Set a name for the node if you don't like the default
    * Set the interval to be the same as the polling interval in `config.ini`, remembering that it is in seconds in - eg. `config.ini` would be 5 minutes here
4. Go to the [Feeds](https://emoncms.org/feed) page (follow the link or find it on the "setup" menu):
   ![feeds](https://cloud.githubusercontent.com/assets/1401069/16238550/c2c71c3e-37d8-11e6-8b82-3e35e9cbc68d.png)
5. All you current actual and target temperature feeds will be in one table. You can edit each line and add a Tag and rename the display name by using the pencil icon. You might, for example, tag all the radiator zones as "Heating".  
   This step is optional.
6. At this point emoncms is now logging all your data and you can start to create graphs.  
   The easiest way to see a graph is to click on one of the eye icons next to a value you want to see on the  [Feeds](https://emoncms.org/feed) page:
   ![graph](https://cloud.githubusercontent.com/assets/1401069/16238552/c4d7b29a-37d8-11e6-866c-06c2d73a1d04.png)
   You can add or remove other feeds to e.g. compare target vs actual temp, compare different rooms etc.
7. You can now create dashboards to create more permanent graphs and do other visualisations such as using gauges to show current temps using the jgauge widget:
   ![dashboard](https://cloud.githubusercontent.com/assets/1401069/16238570/c807bbfe-37d8-11e6-84be-7e5acc9875ee.png)
   Or graphing all of your zones over a period of time using the multigraph visualisation:
   ![allzones](https://cloud.githubusercontent.com/assets/1401069/16238572/ca060faa-37d8-11e6-920a-ccb19fb030b0.png)

_<sub>* Thanks to bmccluskey from the automatedhome.co.uk for these excellent instructions.</sub>_


## Changelog
### 2.0.0 (2022-12-28)
- Upgraded to Python 3.9
- Additional logging and bug fixes
### 1.0.0 (2017)
Initial release