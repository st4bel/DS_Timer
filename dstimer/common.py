import os
import subprocess
from dstimer import __stdOptions__, __key__
import json
from dstimer import world_data
import numpy as np
from datetime import datetime
import requests
import hashlib

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"

escape_table = {
    "?" : "&63#",
    ":" : "&58#",
    "*" : "&42#",
    "|" : "&124#",
    "." : "&46#",
    " " : "&00#"
    #/\:*"<>|
}

unitnames = ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"]
unit_bh = {"spear" : 1, "sword" : 1, "axe" : 1, "archer" : 1, "spy" : 2, "light" : 4, "marcher" : 5, "heavy" : 6, "ram" : 5, "catapult" : 8, "knight" : 10, "snob" : 100}
stat_URL = "http://ds-kalation.de/stat_receive_Timer_0.6.2.php"

def get_root_folder():
    return os.path.join(os.path.expanduser("~"), ".dstimer")

def create_folder_structure():
    """Create all folders needed by DS_Timer

    Currently this creates a '.dstimer' folder in the user's home directory
    on all platforms.
    """
    root = get_root_folder()
    os.makedirs(root, exist_ok=True)
    folders = ["schedule", "expired", "cache", "keks", "logs", "pending", "failed","templates","trash","world_data"]
    for folder in folders:
        os.makedirs(os.path.join(root, folder), exist_ok=True)

def reset_folders():
    root = get_root_folder()
    subprocess.Popen(r"explorer "+root)


def filename_escape(name):
    return "".join(escape_table.get(c,c) for c in name)

def filename_unescape(name):
    for c in escape_table:
        name = name.replace(escape_table[c], c)
    return name

def read_options():
    file = os.path.join(get_root_folder(), "options.txt")
    try:
        if not os.path.exists(file):
            write_options()
        with open(file) as fd:
            options = json.load(fd)
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
    points = np.floor(points/np.power(10,np.floor(np.log10(points))))*np.power(10,np.floor(np.log10(points)))
    h = hashlib.sha256()
    h.update(bytes(player_id+__key__, "utf-8"))
    stats = {
        "p" : int(points),
        "ts" : str(int((datetime.utcnow() - datetime(1970,1,1)).total_seconds())),
        "pl" : h.hexdigest(),
        "a" : "cookie_set",
        "s" : domain
    }
    return stats

def send_stats(stats):
    response = requests.get(url = stat_URL, params = stats)
    return response
