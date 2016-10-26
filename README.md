# DS-Timer

[![Appveyor](https://ci.appveyor.com/api/projects/status/github/st4bel/DS_Timer?svg=true)](https://ci.appveyor.com/project/st4bel/ds-timer)
[![GitHub release](https://img.shields.io/github/release/st4bel/DS_Timer.svg)]()

![Crow](dstimer/static/crow.png)

## Download and Run

```
git clone https://github.com/st4bel/DS_Timer.git
cd DS_Timer
pip install -r requirements.txt
python dstimer_server.py
```

### Requirements for Windows
Install [Python 3.4 or higher](https://www.python.org/downloads/).
Make sure `python` and `pip` are available on the command line (`cmd.exe`):
```
echo %PATH%
```
This should contain `%localappdata%\Programs\Python\Python35-32` and
`%localappdata%\Programs\Python\Python35-32\Scripts` or something
similar.

[Download a git client for Windows.](https://git-scm.com/downloads)

## Example JSON

```json
{
    "domain": "de132.die-staemme.de",
    "player": "Nickname",
    "type": "attack",
    "arrival_time": "2016-10-12T17:30:00",
    "departure_time": "2016-10-12T16:49:45",
    "source_id": 1234,
    "source_coord": {
        "y": 200,
        "x": 300
    },
    "target_id": 12345,
    "target_coord": {
        "x": 200,
        "y": 100
    },
    "units": {
        "spear": 100
    }
}
```

## Credits
Icons made by <a href="http://www.freepik.com" title="Freepik">Freepik</a> from <a href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a>
