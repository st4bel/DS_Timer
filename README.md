# DS-Timer

[![Appveyor](https://ci.appveyor.com/api/projects/status/github/st4bel/DS_Timer?svg=true)](https://ci.appveyor.com/project/st4bel/ds-timer)
[![GitHub release](https://img.shields.io/github/release/st4bel/DS_Timer.svg)]()

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.6/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.6)

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
    "departure_time": "2020-04-30T23:54:13.000",
    "domain": "de132.die-staemme.de",
    "force": false,
    "units": {
        "spy": "10"
    },
    "vacation": "0",
    "target_id": 12345,
    "type": "attack",
    "source_coord": {
        "y": 376,
        "x": 487
    },
    "player_id": "1000456649",
    "player": "st4bel",
    "target_coord": {
        "y": 375,
        "x": 489
    },
    "source_id": 12346,
    "sitter": "0",
    "arrival_time": "2020-05-01T00:14:20"
}
]
```

## Credits
Icons made by <a href="http://www.freepik.com" title="Freepik">Freepik</a> from <a href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a>

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.0/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.0)

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.2/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.2)

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.4/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.4)

[![Github Releases (by Release)](https://img.shields.io/github/downloads/st4bel/ds_timer/v0.6.5/total.svg)](https://github.com/st4bel/ds_timer/releases/tag/v0.6.5)
