# Console Plugin

Writes the temperatures to the console in the form:
<date/time in UTC> Zone1 (actual1 A, target1 T) Zone2 (actual2 A, target2 T)....Hot Water (actual A, target (or OFF)) Outside (actual)

## Example output
```
2016-06-05 15:17:31 Kitchen (21.2 A, 12.0 T) Hot Water (45.0, 55) Outside (21.3)
2016-06-05 15:27:31 Kitchen (21.0 A, 12.0 T) Hot Water (45.0, OFF) Outside (21.3)
```

This tells me that at 15:17:31 UTC (16:17:31 local time in the UK) on 5th June 2016, the Kitchen was 21.2 degrees, target 12.0 (heating off presumably), 
the hot water is 45 degrees, target 55 (HW will be on trying to reach this temp) and outside it is 21.3 degrees

Then 10 minutes later the Kitchen temp has dropped by 0.2 degrees and hot water is now OFF

## config.ini settings
```
[Console]
disabled=<true to disable it, false to enable>
```

## Changelog
### 1.0.0 (2022-12-28)
Initial release
