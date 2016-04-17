## Download and Run

```
git clone https://github.com/st4bel/DS_Timer.git
cd DS_Timer
python daemon.py
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

Then install the required Python packages (using `cmd.exe`):
```
pip install requests beautifulsoup4 ntplib
```

[Download a git client for Windows.](https://git-scm.com/downloads)

### Requirements for Debian/Ubuntu
```
sudo apt-get install git python3
sudo pip install requests beautifulsoup4 ntplib
```
