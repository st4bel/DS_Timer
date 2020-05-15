# DS-Timer

[![Appveyor](https://ci.appveyor.com/api/projects/status/github/st4bel/DS_Timer?svg=true)](https://ci.appveyor.com/project/st4bel/ds-timer)
[![GitHub release](https://img.shields.io/github/release/st4bel/DS_Timer.svg)]()

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.1/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.1)

![Crow](dstimer/static/crow.png)

## Using Releases for simple user

Download the "dstimer_server.exe" of our latest [release](https://github.com/st4bel/DS_Timer/releases) and run it. Open the following address in your favorit browser: [127.0.0.1:5000](127.0.0.1:5000). Follow the instructions shown on the new page (up to now only in german).

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
[{
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
},
{
    "domain": "de132.die-staemme.de",
    "player": "Nickname",
    "type": "attack",
    "arrival_time": "2016-10-12T17:30:00",
    "departure_time": "2016-10-12T16:49:45",
    "source_id": 1233,
    "source_coord": {
        "y": 230,
        "x": 300
    },
    "target_id": 12341,
    "target_coord": {
        "x": 200,
        "y": 120
    },
    "units": {
        "spear": 100
    }
}
]
```

## Credits
Icons made by <a href="http://www.freepik.com" title="Freepik">Freepik</a> from <a href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a>

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.0/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.0)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.5.1/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.5.1)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.5.0/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.5.0)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.4.8/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.4.8)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.4.6.5/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.4.6.5)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/0.4.6.4/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/0.4.6.4)
[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.4.6/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.4.6)
