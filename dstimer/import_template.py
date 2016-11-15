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
from dstimer import common
from dstimer import import_action

def import_from_workbench(text):
    tree = ET.fromstring(text)
    template = {}
    units = {}
    for tree_template in tree:
        template["name"] = tree_template.get("name")
        for tree_unit in tree_template.find("attackElements"):
            filled = False
            if tree_unit.get("fix") != "0":
                filled = True
                if tree_unit.get("fixAmount") != "-1":
                    units[tree_unit.get("unit")] = tree_unit.get("fixAmount")
                else:
                #dynamische Truppenangebe: Alle+-+100;
                    text = tree_unit.get("dynAmount")
                    text = text.replace("+","").replace("Alle","")
                    units[tree_unit.get("unit")] = text
        template["units"]=units;
        if filled:
            import_as_json(template)



#<stdAttacks>
#   <stdAttack name="Off" icon="2">
#       <attackElements>
#           <attackElement unit="spear" fixAmount="-1" dynAmount="Alle"/>


def import_as_json(dict):
    if dict["name"] != "":
        path = os.path.join(os.path.expanduser("~"), ".dstimer", "templates", dict["name"]+"_"+import_action.random_id(6)+".template")
        with open(path, "w") as fd:
            json.dump(dict["units"], fd, indent=2)

def remove_by_id(id):
    template_path = os.path.join(os.path.expanduser("~"), ".dstimer", "templates")
    trash_path = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    for file in os.listdir(template_path):
        if id in file:
            os.rename(os.path.join(template_path, file), os.path.join(trash_path, file))
