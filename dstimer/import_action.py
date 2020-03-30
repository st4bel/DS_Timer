#!/usr/bin/env python3
import sys
import json
import os
import math
import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
import dateutil.parser
import random, string
from dstimer import common, world_data
from dstimer.intelli_unit import get_bh_all
#import numpy as np

def distance(source, target):
    return math.sqrt(pow(target["x"] - source["x"], 2) + pow(target["y"] - source["y"], 2))

def is_zero(format):
    return str(format) == "0" or format == "=0" or format == ""

def speed(units, type, stats):
    if type == "support" and not is_zero(units.get("knight", 0)):
        # travel with knight speed if there is a knight
        return stats["knight"]
    slowest = 0
    for unit in units:
        if not is_zero(units[unit]) and stats[unit] > slowest:
            slowest = stats[unit]
    return slowest

def runtime(speed, distance):
    return timedelta(seconds=round(60 * speed * distance))

def get_unit_info(domain):
    headers = {"user-agent": common.USER_AGENT}
    response = requests.get("https://" + domain + "/interface.php?func=get_unit_info", headers=headers)
    tree = ET.fromstring(response.content)
    units = dict()
    for unit in tree:
        units[unit.tag] = round(float(unit.find("speed").text))
    return units

def get_cached_unit_info(domain):
    directory = os.path.join(common.get_root_folder(), "cache")
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
    action["source_coord"]["x"] = int(action["source_coord"]["x"])
    action["source_coord"]["y"] = int(action["source_coord"]["y"])
    action["target_coord"]["x"] = int(action["target_coord"]["x"])
    action["target_coord"]["y"] = int(action["target_coord"]["y"])

    units_to_delete = []
    for unit, amount in action["units"].items():
        if is_zero(amount):
            units_to_delete.append(unit)
    for unit in units_to_delete:
        del action["units"][unit]
    unit_info = get_cached_unit_info(action["domain"])
    duration = runtime(speed(action["units"], action["type"], unit_info),
        distance(action["source_coord"], action["target_coord"]))
    if "departure_time" not in action:
        action["departure_time"] = (dateutil.parser.parse(action["arrival_time"]) - duration).isoformat()
    if "arrival_time" not in action:
        action["arrival_time"] = (dateutil.parser.parse(action["departure_time"]) + duration).isoformat()

def random_id(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))
def random_milliseconds(border):
    ms = int("".join(random.choice(string.digits) for i in range(3)))
    if ms<border:
        ms=ms+2*border
    elif ms>1000-border:
        ms=ms-2*border
    return str(ms)

def import_from_text(text, rand_mill=False):
    actions = json.loads(text)
    try:  #handhabung von multi-input
        bla=actions[0]
    except:
        actions=json.loads("["+text+"]")
    for action in actions:
        autocomplete(action)
        if rand_mill:
            mill = timedelta(seconds=random.random()-0.5)
            action["departure_time"] = (dateutil.parser.parse(action["departure_time"]) + mill).isoformat()
            action["arrival_time"] = (dateutil.parser.parse(action["arrival_time"]) + mill).isoformat()
        filename = dateutil.parser.parse(action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

        directory = os.path.join(common.get_root_folder(), "schedule")
        file = os.path.join(directory, filename)
        with open(file, "w") as fd:
            json.dump(action, fd, indent=4)
def import_wb_action(text,name):
    #splitting text for [*]
    s = text.split("[/**]")
    actions_text = s[1].split("[/*]")
    action={}
    for action_text in actions_text[:-1]:
        columns = action_text.split("[|]")
        if "Angriff" in columns[1]:
            action["type"]="attack"
        else:
            action["type"]="support"
        action["source_coord"]={}
        action["target_coord"]={}
        action["source_coord"]["x"]=columns[3].split("|")[0].split("]")[1]
        action["source_coord"]["y"]=columns[3].split("|")[1].split("[")[0]
        action["target_coord"]["x"]=columns[4].split("|")[0].split("]")[1]
        action["target_coord"]["y"]=columns[4].split("|")[1].split("[")[0]
        action["domain"] = columns[6].split("/")[2]
        params = columns[6].split('"')[1].split("?")[1].split("&")
        a = {}
        for param in params:
            a[param.split("=")[0]]=param.split("=")[1]
        action["source_id"] = int(a["village"])
        action["target_id"] = int(a["target"])
        date=columns[5].split(" um ")
        date[0] = date[0].split(".")
        #action["departure_time"] = "20"+date[0][2]+"-"+date[0][1]+"-"+date[0][0]+"T"+date[1]+"."+random_milliseconds(100)
        action["departure_time"] = "20"+date[0][2]+"-"+date[0][1]+"-"+date[0][0]+"T"+date[1]
        if len(date[1].split('.'))==1: #falls keine millisekunden übergeben
            action["departure_time"] += "."+random_milliseconds(100)
        action["units"] = get_troups_from_template(columns[1].split("(")[1].split(")")[0])
        action["player"]=name
        action["player_id"] = world_data.get_player_id(action["domain"],action["player"])
        action["force"] = False
        action["vacation"] = "0"
        action["sitter"] = "0"
        if "arrival_time" in action:
            del action["arrival_time"] # no arrival time in workbench export
        autocomplete(action)
        filename = dateutil.parser.parse(action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

        directory = os.path.join(common.get_root_folder(), "schedule")
        file = os.path.join(directory, filename)
        with open(file, "w") as fd:
            json.dump(action, fd, indent=4)

def import_from_ui(action, rand_mill = False, id = None):
    autocomplete(action)
    if rand_mill:
        mill = timedelta(seconds=random.random()-0.5)
        action["departure_time"] = (dateutil.parser.parse(action["departure_time"]) + mill).isoformat()
        action["arrival_time"] = (dateutil.parser.parse(action["arrival_time"]) + mill).isoformat()
    filename = dateutil.parser.parse(action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + (id if id else random_id(6)) + ".txt"

    directory = os.path.join(common.get_root_folder(), "schedule")
    if id:
        for file in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file)) and id in file:
                os.remove(os.path.join(directory, file))
                break
    file = os.path.join(directory, filename)
    with open(file, "w") as fd:
        json.dump(action, fd, indent=4)

def get_troups_from_template(template_name):
    path = os.path.join(os.path.expanduser("~"), ".dstimer", "templates")
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)) and filename[:-16] == template_name:
            with open(os.path.join(path, filename)) as fd:
                units = json.load(fd)
            return units
    raise NameError('Vorlage "'+template_name+'" nicht vorhanden.')

def get_attack_size(units):
    bh = get_bh_all(units)
    if not bh:
        return ""
    if bh <= 1000:
        return "_small"
    elif bh > 1000 and bh <= 5000:
        return "_medium"
    else:
        return "_big"

    #5[|]Angriff (Clean-Off)[|]Ramme[|][coord]446|290[/coord][|][coord]604|388[/coord][|]20.04.16 um 23:16:43.863[|][url="https://de118.die-staemme.de/game.php?village=49989&screen=place&mode=command&target=23476"]Versammlungsplatz[/url]
