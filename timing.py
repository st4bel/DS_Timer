import math
import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
import ntplib
import threading
import dateutil.parser
import os
import json
import datetime
import time
import attack
import socket

def distance(source, target):
    return math.sqrt(pow(target[0] - source[0], 2) + pow(target[1] - source[1], 2))

def speed(units, attack_or_support, stats):
    if not attack_or_support and units.get("knight", 0) > 0:
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
    cache_diectory =  os.path.join(os.path.expanduser("~"), ".dstimer", "cache")
    cache_file = os.path.join(cache_diectory, domain)
    try:
        # try to load cached file
        with open(cache_file) as file:
            return json.load(file)
    except:
        # otherwise load the actual data
        unit_info = get_unit_info(domain)
        os.makedirs(cache_diectory, exist_ok=True)
        # and save it in a cache file
        with open(cache_file, "w") as file:
            json.dump(unit_info, file)
        return unit_info

def get_local_offset():
    client = ntplib.NTPClient()
    response = client.request("pool.ntp.org", version=3)
    return timedelta(seconds=response.offset)

def get_ping(domain):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    before = datetime.datetime.now()
    s.connect((domain, 80))
    after = datetime.datetime.now()
    s.shutdown()
    s.close()
    return after - before

class Action:
    def __init__(self, json):
        self.source_id = json["source_id"]
        self.source_coord = (json["source_coord"]["x"], json["source_coord"]["y"])
        self.target_id = json["target_id"]
        self.target_coord = (json["target_coord"]["x"], json["target_coord"]["y"])
        self.units = json["units"]
        if json["type"] == "attack":
            self.attack_or_support = True
        elif json["type"] == "support":
            self.attack_or_support = False
        else:
            raise ValueError("Unknown action type. Must be attack or support")
        if "arrival_time" in json:
            self.arrival_time = dateutil.parser.parse(json["arrival_time"])
        elif "departure_time" in json:
            self.departure_time = dateutil.parser.parse(json["departure_time"])
        else:
            raise ValueError("Missing arrival_time or departure_time")

    def unit(self, name):
        return self.units.get(name, 0)

    def autocomplete(self, keks):
        if not hasattr(self, "departure_time"):
            unit_info = get_cached_unit_info(keks["domain"])
            duration = runtime(speed(self.units, self.attack_or_support, unit_info),
                distance(self.source_coord, self.target_coord))
            self.departure_time = self.arrival_time - duration

class SendActionThread(threading.Thread):
    def __init__(self, keks, action):
        threading.Thread.__init__(self)
        self.keks = keks
        self.action = action

    def run(self):
        self.action.autocomplete(self.keks)

        (units, form) = attack.get_place_screen(self.keks, self.action.source_id)
        (action, data) = attack.get_confirm_screen(self.keks, form, self.action.units,
            self.action.target_coord[0], self.action.target_coord[1], self.action.attack_or_support)

        offset = get_local_offset()
        ping = get_ping(self.keks["domain"])
        real_departure = self.action.departure_time - offset - ping

        print(real_departure)

        while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=5):
            time_left = real_departure - datetime.datetime.now()
            print(time_left)
            time.sleep((time_left / 2).total_seconds())

        print(datetime.datetime.now())
        attack.just_do_it(self.keks, action, data)
        print(datetime.datetime.now())
