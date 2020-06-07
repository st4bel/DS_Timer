# DS-Timer package
import requests
from version_parser import Version

__version__ = "v0.6.3-dev"

__key__ = "insert key here lol"
__stdOptions__ = {"show_donate": True, "version": __version__, "LZ_reduction" : {}, "min_time_diff" : 150}

try:
    request_release = requests.get("https://api.github.com/repos/st4bel/DS_Timer/releases/latest")
    json_release    = request_release.json()
    __needUpdate__  = Version(__version__) < Version(json_release["name"])
except: # if latest Version or current Version cant be parsed
    __needUpdate__  = False
