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

def import_template_from_workbench():
    todo=1

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
