import math
import requests
import xml.etree.ElementTree as ET
from datetime import timedelta

def distance(source_x, source_y, target_x, target_y):
    return math.sqrt(pow(target_x - source_x, 2) + pow(target_y - source_y, 2))

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
