# CSV Plugin

Writes the temperatures to a .csv file.

The first column is always "Time" and is the UTC date and time
For each zone then, you get a column &lt;zone name&gt; [A] for the actual measured temperature.
If a target temperature is available then you get another column  &lt;zone name&gt; [T] representing the target temperature.
An input plugin measuring the outside temperature for example won't have a target temperature available.

## Example output
```
Time,Kitchen [A],Kitchen [T],Hot Water [A],Hot Water [T],Outside
2016-06-05 15:17:31,21.2,12.0,45.0,55.0,21.3
```

This tells me that at 15:17:31 UTC (16:17:31 local time in the UK) on 5th June 2016, the Kitchen was 21.2 degrees, target 12.0 (heating off presumably),
the hot water is 45 degrees, target 55 (HW will be on trying to reach this temp) and outside it is 21.3 degrees

## config.ini settings
```
[Csv]
filename=<absolute or relative name of file to write to>
```

## Changelog
### 3.0.0 (2022-02-06)
- Rewritten to use the new plugin model
### 2.0.0 (2021-12-28)
- Upgraded to Python 3.9
- Additional logging and bug fixes
### 1.0.0 (2017)
Initial release
