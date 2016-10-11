#!/usr/bin/env python3
import sys
import json
import os
import math
import pyperclip
import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
import dateutil.parser
import random, string

def distance(source, target):
    return math.sqrt(pow(target["x"] - source["x"], 2) + pow(target["y"] - source["y"], 2))

def speed(units, type, stats):
    if type == "support" and units.get("knight", 0) > 0:
        # travel with knight speed if there is a knight
        return stats["knight"]
    slowest = 0
    for unit in units:
        if units[unit] > 0 and stats[unit] > slowest:
            slowest = stats[unit]
    return slowest

def runtime(speed, distance):
    return timedelta(seconds=round(60 * speed * distance))

def get_unit_info(domain):
    response = requests.get("https://" + domain + "/interface.php?func=get_unit_info")
    tree = ET.fromstring(response.content)
    units = dict()
    for unit in tree:
        units[unit.tag] = round(float(unit.find("speed").text))
    return units

def get_cached_unit_info(domain):
    directory =  os.path.join(os.path.expanduser("~"), ".dstimer", "cache")
    file = os.path.join(directory, domain)
    try:
        # try to load cached file
        with open(file) as fd:
            return json.load(fd)
    except:
        # otherwise load the actual data
        unit_info = get_unit_info(domain)
        os.makedirs(directory, exist_ok=True)
        # and save it in a cache file
        with open(file, "w") as fd:
            json.dump(unit_info, fd)
        return unit_info

def autocomplete(action):
    """Add missing information about an action like departure time"""
    unit_info = get_cached_unit_info(action["domain"])
    duration = runtime(speed(action["units"], action["type"], unit_info),
        distance(action["source_coord"], action["target_coord"]))

    if "departure_time" not in action:
        action["departure_time"] = (dateutil.parser.parse(action["arrival_time"]) - duration).isoformat()
    if "arrival_time" not in action:
        action["arrival_time"] = (dateutil.parser.parse(action["departure_time"]) + duration).isoformat()

def random_id(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))

def import_from_text(text):
    action = json.loads(text)
    autocomplete(action)

    filename = dateutil.parser.parse(action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

    directory = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    file = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    with open(file, "w") as fd:
        json.dump(action, fd, indent=4)

def main():
    import_from_text(pyperclip.paste())

if __name__ == "__main__":
    main()
