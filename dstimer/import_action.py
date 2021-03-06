#!/usr/bin/env python3
import sys
import json
import os
import math
import requests
import xml.etree.ElementTree as ET
import logging
from datetime import timedelta, datetime
import dateutil.parser
import random, string
from dstimer import common, world_data, db
from dstimer.intelli_unit import get_bh_all
from dstimer.models import Attacks, Player, Template
from flask import flash
from bs4 import BeautifulSoup


logger = logging.getLogger("dstimer")


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


def runtime(speed, distance, domain):
    return timedelta(
        seconds=round(distance *
                      (speed /
                       (world_data.get_unit_speed(domain) * world_data.get_world_speed(domain))) *
                      60))


def get_unit_info(domain):
    headers = {"user-agent": common.USER_AGENT}
    response = requests.get("https://" + domain + "/interface.php?func=get_unit_info",
                            headers=headers)
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


def get_LZ_factor(action):
    LZ = common.read_options()["LZ_reduction"]
    if action["type"] != "support" or LZ == {}:
        return 1
    if LZ["domain"] != action["domain"]:
        return 1
    if LZ["player"] != "" and int(LZ["player_id"]) != int(
            world_data.get_village_owner(action["domain"], action["target_id"])):
        return 1    #
    if "arrival_time" not in action:
        if dateutil.parser.parse(action["departure_time"]) > dateutil.parser.parse(LZ["until"]):
            return 1
    if "departure_time" not in action:
        duration = runtime(
            speed(action["units"], action["type"], get_cached_unit_info(action["domain"])) /
            (1 + int(LZ["magnitude"]) / 100),
            distance(action["source_coord"], action["target_coord"]), action["domain"])
        departure_time = dateutil.parser.parse(action["arrival_time"]) - duration
        if departure_time > dateutil.parser.parse(LZ["until"]):
            return 1
    return 1 + int(LZ["magnitude"]) / 100


def autocomplete(action):
    """Add missing information about an action like departure time"""
    if "source_coord" not in action:
        action["source_coord"] = world_data.get_village_coord_from_id(action["domain"], action["source_id"])
    if "target_coord" not in action:
        action["target_coord"] = world_data.get_village_coord_from_id(action["domain"], action["target_id"])
    action["source_coord"]["x"] = int(action["source_coord"]["x"])
    action["source_coord"]["y"] = int(action["source_coord"]["y"])
    action["target_coord"]["x"] = int(action["target_coord"]["x"])
    action["target_coord"]["y"] = int(action["target_coord"]["y"])

    if "units" not in action:
        action["units"] = dict()
    units_to_delete = []
    for unit, amount in action["units"].items():
        if is_zero(amount):
            units_to_delete.append(unit)
    for unit in units_to_delete:
        del action["units"][unit]
    unit_info = get_cached_unit_info(action["domain"])

    duration = runtime(
        speed(action["units"], action["type"], unit_info) ,
        distance(action["source_coord"], action["target_coord"]), action["domain"])
    if "departure_time" not in action:
        action["departure_time"] = (dateutil.parser.parse(action["arrival_time"]) -
                                    duration).isoformat()
    if "arrival_time" not in action:
        action["arrival_time"] = (dateutil.parser.parse(action["departure_time"]) +
                                  duration).isoformat()
    if "next_attack" not in action:
        action["next_attack"] = False
    if "building" not in action:
        action["building"] = common.read_options()["kata-target"]
    if "save_default_attack_building" not in action:
        action["save_default_attack_building"] = 0
    if "sitter" not in action:
        action["sitter"] = "0"
    if "vacation" not in action:
        action["vacation"] = "0"
    if "force" not in action:
        action["force"] = False


def random_id(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


def random_milliseconds(border):
    ms = int("".join(random.choice(string.digits) for i in range(3)))
    if ms < border:
        ms = ms + 2 * border
    elif ms > 1000 - border:
        ms = ms - 2 * border
    return str(ms)


def import_from_text(text, rand_mill=False):
    actions = json.loads(text)
    try:    #handhabung von multi-input
        bla = actions[0]
    except:
        actions = json.loads("[" + text + "]")
    for action in actions:
        autocomplete(action)
        if rand_mill:

            mill = timedelta(seconds=random.random() - 0.5)
            action["departure_time"] = (dateutil.parser.parse(action["departure_time"]) +
                                        mill).isoformat()
            action["arrival_time"] = (dateutil.parser.parse(action["arrival_time"]) +
                                      mill).isoformat()
        filename = dateutil.parser.parse(
            action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

        directory = os.path.join(common.get_root_folder(), "schedule")
        file = os.path.join(directory, filename)
        #with open(file, "w") as fd:
        #    json.dump(action, fd, indent=4)
        add_attack_to_db(action)




def import_from_tampermonkey(action):
    autocomplete(action)
    filename = dateutil.parser.parse(
        action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

    directory = os.path.join(common.get_root_folder(), "schedule")
    file = os.path.join(directory, filename)
    with open(file, "w") as fd:
        json.dump(action, fd, indent=4)


def import_wb_action(text, name, catapult_target="default", action_type = "attack"):
    #splitting text for [*]
    s = text.split("[/**]")
    actions_text = s[1].split("[/*]")
    action = {}
    for action_text in actions_text[:-1]:
        columns = action_text.split("[|]")
        #if "Angriff" in columns[1]:
        #    action["type"] = "attack"
        #else:
        #    action["type"] = "support"
        action["type"] = action_type
        action["source_coord"] = {}
        action["target_coord"] = {}
        action["source_coord"]["x"] = columns[3].split("|")[0].split("]")[1]
        action["source_coord"]["y"] = columns[3].split("|")[1].split("[")[0]
        action["target_coord"]["x"] = columns[4].split("|")[0].split("]")[1]
        action["target_coord"]["y"] = columns[4].split("|")[1].split("[")[0]
        action["domain"] = columns[6].split("/")[2]
        params = columns[6].split('"')[1].split("?")[1].split("&")
        a = {}
        for param in params:
            a[param.split("=")[0]] = param.split("=")[1]
        action["source_id"] = int(a["village"])
        action["target_id"] = int(a["target"])
        date = columns[5].split(" um ")
        date[0] = date[0].split(".")
        #action["departure_time"] = "20"+date[0][2]+"-"+date[0][1]+"-"+date[0][0]+"T"+date[1]+"."+random_milliseconds(100)

        action["departure_time"] = "20" + date[0][2] + "-" + date[0][1] + "-" + date[0][
            0] + "T" + date[1]
        if len(date[1].split('.')) == 1:
            action["departure_time"] += "." + random_milliseconds(100)

        if "(" in columns[1]:
            action["units"] = get_troups_from_template(columns[1].split("(")[1].split(")")[0])
            action["template_name"] = columns[1].split("(")[1].split(")")[0]
        else:
            action["units"] = get_troups_from_template(columns[1])
            action["template_name"] = columns[1]

        if name != "":
            action["player"] = name
            action["player_id"] = world_data.get_player_id(action["domain"], action["player"])
        else: 
            action["player_id"] = world_data.get_village_owner(action["domain"], action["source_id"])
            action["player"] = world_data.get_player_name(action["domain"], action["player_id"])
            name = action["player"]
        
        action["force"] = False
        action["vacation"] = "0"
        action["sitter"] = "0"
        action["building"] = catapult_target
        if "arrival_time" in action:
            del action["arrival_time"]    # no arrival time in workbench export
        autocomplete(action)
        #filename = dateutil.parser.parse(
        #    action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"

        #directory = os.path.join(common.get_root_folder(), "schedule")
        #file = os.path.join(directory, filename)
        #with open(file, "w") as fd:
        #    json.dump(action, fd, indent=4)
        add_attack_to_db(action)

def import_from_workbench_html(text, catapult_target, action_type = "attack"):
    soup = BeautifulSoup(text, "html.parser")
    links = soup.find_all("a")
    dep_times = soup.find_all("td", {"class": "time_left"})
    counter = 0
    for link in links:
   #     link = links[counter]
    #    dep_time = demp_times
    #    counter = counter + 1
        if link.text == "Versammlungsplatz":
            dep_time = dep_times[counter]
            counter = counter + 1
            action = dict()
            action["units"] = dict()
            link_href = link["href"].split("/")
            action["domain"] = link_href[2]
            params = link_href[-1].split("?")[1].split("&")
            for param in params:
                arg = param.split("=")
                if "village" in arg[0]:
                    action["source_id"] = arg[1]
                elif "target" in arg[0]:
                    action["target_id"] = arg[1]
                else:
                    for unit in common.unitnames:
                        if unit in arg[0]:
                            action["units"][unit] = arg[1]
            action["player_id"] = world_data.get_village_owner(action["domain"], action["source_id"])
            action["player"] = world_data.get_player_name(action["domain"], action["player_id"])
            action["building"] = catapult_target
            action["departure_time"] = datetime.strptime(dep_time.text, "%d.%m.%Y %H:%M:%S").isoformat()
            action["type"] = action_type
            autocomplete(action)

            #directory = os.path.join(common.get_root_folder(), "schedule")
            #filename = dateutil.parser.parse(action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + random_id(6) + ".txt"
            #file = os.path.join(directory, filename)
            #with open(file, "w") as fd:
            #    json.dump(action, fd, indent=4)
            add_attack_to_db(action)
            

def import_from_ui(action, rand_mill=False, id=None):
    autocomplete(action)
    if action["type"] == "multiple_attacks":
        directory = os.path.join(common.get_root_folder(), "temp_action")
    else:
        directory = os.path.join(common.get_root_folder(), "schedule")
    if id:    # removing old file
        for file in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file)) and id in file:
                os.remove(os.path.join(directory, file))
                break
    else:
        id = random_id(6)
    if rand_mill:
        mill = timedelta(seconds=random.random() - 0.5)
        action["departure_time"] = (dateutil.parser.parse(action["departure_time"]) +
                                    mill).isoformat()
        action["arrival_time"] = (dateutil.parser.parse(action["arrival_time"]) + mill).isoformat()
    action["id"] = id
    filename = dateutil.parser.parse(
        action["departure_time"]).strftime("%Y-%m-%dT%H-%M-%S-%f") + "_" + id + ".txt"
    file = os.path.join(directory, filename)
    with open(file, "w") as fd:
        json.dump(action, fd, indent=4)
    return id


def get_troups_from_template(template_name):
    t = Template.query.filter_by(name=template_name).first()
    return t.get_units()
    raise NameError('Vorlage "' + template_name + '" nicht vorhanden.')


def get_attack_size(units):
    bh = get_bh_all(units)
    if not bh:
        return ""
    if bh < 1000:
        return "_small"
    elif bh >= 1000 and bh <= 5000:
        return "_medium"
    else:
        return "_large"


def check_LZ(LZ):
    if LZ["player"] != "":
        player_id = world_data.get_player_id(domain=LZ["domain"], playername=LZ["player"])
        if player_id == None:
            return {}
        LZ["player_id"] = player_id
    else:
        LZ["player_id"] = 0
    if datetime.now() > dateutil.parser.parse(LZ["until"]):
        return {}
    try:
        magnitude = int(LZ["magnitude"])
        if magnitude < 0 or magnitude > 50:
            return {}
    except:
        return {}
    return LZ


def add_attack_to_db(action):
    autocomplete(action)
    try:
        player = Player.query.filter_by(domain = action["domain"], player_id = int(action["player_id"])).first()
    except:
        flash("Spieler {} auf Server {} nicht gefunden. Bitte zuerst Keks importieren!".format(action["player"], action["domain"]))
        return
    a = Attacks(
        departure_time = dateutil.parser.parse(action["departure_time"]),
        arrival_time = dateutil.parser.parse(action["arrival_time"]),
        source_id = action["source_id"],
        source_coord_x = action["source_coord"]["x"],
        source_coord_y = action["source_coord"]["y"],
        target_id = action["target_id"],
        target_coord_x = action["target_coord"]["x"],
        target_coord_y = action["target_coord"]["y"],
        #player_id = int(action["player_id"]),
        #player = action["player"],
        player = player,
        building = action["building"],
        save_default_attack_building = action["save_default_attack_building"],
        force = False, 
        #domain = action["domain"], 
        type = action["type"], 
        status = "scheduled"
    )

    a.units = str(action["units"])

    if "template_name" in action:
        try:
            a.template = Template.query.filter_by(name=action["template_name"]).first()
        except:
            flash("Template mit Namen {} nicht gefunden".format(action["template_name"]))
            return

    a.autocomplete()
    if not a.is_expired():
        db.session.add(a)
        db.session.commit()