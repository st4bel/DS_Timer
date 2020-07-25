import os
import requests
from dstimer import common
#import pandas as pd
import urllib.parse
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger("dstimer")


def get_server_files(domain):
    directory = os.path.join(common.get_root_folder(), "world_data", domain)
    os.makedirs(directory, exist_ok=True)
    look_at = ["village", "player"]
    for name in look_at:
        url = "https://" + domain + "/map/" + name + ".txt"
        file = requests.get(url)
        filename = os.path.join(directory, name + ".txt")
        open(filename, "wb").write(file.content)


def get_world_config(domain):
    directory = os.path.join(common.get_root_folder(), "world_data", domain)
    os.makedirs(directory, exist_ok=True)
    url = "https://" + domain + "/interface.php?func=get_config"
    file = requests.get(url)
    filename = os.path.join(directory, "world_config.txt")
    open(filename, "wb").write(file.content)


def refresh_world_data():
    keks_path = os.path.join(common.get_root_folder(), "keks")
    for domain in os.listdir(keks_path):
        get_server_files(domain)
        get_world_config(domain)


def get_unit_speed(domain):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "world_config.txt")
    root = ET.parse(file).getroot()
    for child in root:
        if child.tag == "unit_speed":
            return float(child.text)
    return 1


def get_world_speed(domain):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "world_config.txt")
    root = ET.parse(file).getroot()
    for child in root:
        if child.tag == "speed":
            return float(child.text)
    return 1


def get_villages_of_player(domain, player=None, player_id=None):
    directory = os.path.join(common.get_root_folder(), "world_data", domain)
    os.makedirs(os.path.join(directory, "villages_of_players"), exist_ok=True)
    if player_id == None:
        player_id = get_player_id(domain, player)
    player_id = player_id
    village_data = readfile_norm(os.path.join(directory, "village.txt"))
    villages = []
    for dataset in village_data:
        if player_id == dataset[4]:
            villages.append({
                "id": str(dataset[0]),
                "name": unquote_name(dataset[1]),
                "coord": {
                    "x": str(dataset[2]),
                    "y": str(dataset[3])
                },
                "player_id": str(dataset[4]),
                "points": str(dataset[5])
            })
    return villages


def get_village_owner(domain, village_id):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "village.txt")
    data = readfile_norm(file)
    for dataset in data:
        if int(dataset[0]) == int(village_id):
            return dataset[4]
    return None


def get_player_id(domain, playername):    # SPACE turn into "+" Umlaute into
    file = os.path.join(common.get_root_folder(), "world_data", domain, "player.txt")
    data = readfile_norm(file)
    for dataset in data:
        if quote_name(playername) == dataset[1]:
            return dataset[0]
    return None


def get_player_name(domain, player_id):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "player.txt")
    data = readfile_norm(file)
    for dataset in data:
        if player_id == str(dataset[0]):
            return unquote_name(dataset[1])
    return None


def readfile_norm(filename, delimiter=","):
    data = []
    if os.path.exists(filename):
        with open(filename) as f:
            for line in f:
                dataset = [elt.strip() for elt in line.split(delimiter)]
                data.append(dataset)
    return data


def quote_name(name):
    s_name = name.split(" ")
    name = ""
    for s in s_name:
        s = urllib.parse.quote(s)
        name = name + s + "+"
    return name[:-1]


def unquote_name(name):
    s_name = name.split("+")
    name = ""
    for s in s_name:
        s = urllib.parse.unquote(s)
        name = name + s + " "
    return name[:-1]


def get_players(domain):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "player.txt")
    data = readfile_norm(file)
    players = []
    for dataset in data:
        players.append({"id": str(dataset[0]), "name": unquote_name(dataset[1])})
    return players


def get_village_id_from_coords(domain, x, y):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "village.txt")
    data = readfile_norm(file)
    for dataset in data:
        if x == str(dataset[2]) and y == str(dataset[3]):
            return dataset[0]
    return None


def get_village_name_from_id(domain, id):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "village.txt")
    data = readfile_norm(file)
    id = int(id)
    for dataset in data:
        if id == int(dataset[0]):
            return unquote_name(dataset[1])
    return None


def get_player_points(player_id, domain):
    file = os.path.join(common.get_root_folder(), "world_data", domain, "player.txt")
    data = readfile_norm(file)
    for dataset in data:
        if int(player_id) == int(dataset[0]):
            return int(dataset[4])
