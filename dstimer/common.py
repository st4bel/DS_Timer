import os
import subprocess
from dstimer import __stdOptions__, __key__, __version__
import json
from dstimer import world_data
import math
import datetime
import requests
import hashlib
import logging
from version_parser import Version


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"

escape_table = {
    "?": "&63#",
    ":": "&58#",
    "*": "&42#",
    "|": "&124#",
    ".": "&46#",
    " ": "&00#"
    #/\:*"<>|
}

unitnames = [
    "spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult",
    "knight", "snob"
]

buildingnames = [
    "main", "farm", "storage", "place", "barracks", "church", "smith", "wood", "stone", "iron",
    "market", "stable", "wall", "garage", "hide", "snob", "statue", "watchtower"
]

unit_bh = {
    "spear": 1,
    "sword": 1,
    "axe": 1,
    "archer": 1,
    "spy": 2,
    "light": 4,
    "marcher": 5,
    "heavy": 6,
    "ram": 5,
    "catapult": 8,
    "knight": 10,
    "snob": 100
}
stat_URL = "http://ds-kalation.de/stat_receive_Timer_0.6.2.php"


def get_root_folder():
    return os.path.join(os.path.expanduser("~"), ".dstimer")


def get_username(domain):
    directory = os.path.join(common.get_root_folder(), "keks", domain)


def create_folder_structure():
    """Create all folders needed by DS_Timer

    Currently this creates a '.dstimer' folder in the user's home directory
    on all platforms.
    """
    root = get_root_folder()
    os.makedirs(root, exist_ok=True)
    folders = [
        "schedule", "expired", "cache", "keks", "logs", "pending", "failed", "templates", "trash",
        "world_data", "temp_action"
    ]
    for folder in folders:
        os.makedirs(os.path.join(root, folder), exist_ok=True)


def reset_folders():
    root = get_root_folder()
    subprocess.Popen(r"explorer " + root)


def filename_escape(name):
    return "".join(escape_table.get(c, c) for c in name)


def filename_unescape(name):
    for c in escape_table:
        name = name.replace(escape_table[c], c)
    return name


def read_options():
    file = os.path.join(get_root_folder(), "options.txt")
    try:
        if not os.path.exists(file):
            logger.info("creating options.txt")
            write_options()
        with open(file) as fd:
            options = json.load(fd)
        if Version(__version__) > Version(options["version"]):
            logger.info("found an update install it!")
            write_options()
            return __stdOptions__
        return options
    except:
        return __stdOptions__


def write_options(options=__stdOptions__):
    try:
        with open(os.path.join(get_root_folder(), "options.txt"), "w") as fd:
            json.dump(options, fd)
    except:
        return


def create_stats(player_id, domain):
    points = world_data.get_player_points(player_id=player_id, domain=domain)
    points = math.floor(points / math.pow(10, math.floor(math.log10(points)))) * math.pow(
        10, math.floor(math.log10(points)))
    h = hashlib.sha256()
    h.update(bytes(player_id + __key__, "utf-8"))
    stats = {
        "p": int(points),
        "ts": str(int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())),
        "pl": h.hexdigest(),
        "a": __version__ + ": cookie_set",
        "s": domain
    }
    return stats


def send_stats(stats):
    response = requests.get(url=stat_URL, params=stats)
    return response

def parse_timestring(date_string):
    # heute um 22:43:54:442, etc zu datetime
    now = datetime.datetime.now()
    date_string = date_string.split(" um ")
    date = datetime.datetime.today()
    if "morgen" in date_string[0]: # heute: do nothing, morgen: add one, specific date, set
        date = date + datetime.timedelta(days=1)
    elif "heute" not in date_string[0]:
        date = date.replace(month=int(date_string[0].split("am ")[1].split(".")[1]), day=int(date_string[0].split("am ")[1].split(".")[0]))
        if now.month > date.month: # falls im nächsten jahr
            date = date.replace(year=date.year + 1)

    time = date_string[1].split(":")

    date = date.replace(hour = int(time[0]), minute = int(time[1]), second = int(time[2]))

    if len(time) > 3: #milliseconds 
        date = date.replace(microsecond=int(time[3])*1000)
    else:
        date = date.replace(microsecond=0)
    
    return date

def unparse_timestring(date):
    # datetime zu heute um 22:43:54:442, etc
    now = datetime.datetime.now()
    day_string = ""
    if now.date() == date.date():
        day_string = "heute"
    elif now.date() + datetime.timedelta(days=1) == date.date():
        day_string = "morgen"
    else:
        day_string = "am " + str(date.day) + "." + str(date.month) + "."

    time_string = str(date.hour) + ":" + str(date.minute) + ":" + str(date.second) + ":" + str(int(date.microsecond / 1000)).zfill(3) # leading zeros 

    return day_string + " um " + time_string