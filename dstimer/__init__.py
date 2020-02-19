# DS-Timer package
import requests
from version_parser import Version

__version__ = "v0.4.8"

request_release = requests.get("https://api.github.com/repos/st4bel/DS_Timer/releases/latest")
json_release    = request_release.json()
__needUpdate__  = Version(__version__) < Version(json_release["name"])
