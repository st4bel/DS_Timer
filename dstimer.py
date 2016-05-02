import time
import dateutil.parser
import datetime
import json
import requests
from bs4 import BeautifulSoup
import re
import math
import xml.etree.ElementTree as ET
from datetime import timedelta
import ntplib
import threading
import os
import json
import socket

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"

def get_place_screen(session, domain, village_id):
    params = dict(village=village_id, screen="place")
    response = session.get("https://" + domain + "/game.php", params=params)
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.select("form#command-data-form")[0]
    units = dict()
    for input in form.select("input[id^=unit_input_]"):
        units[input["name"]] = int(input.find_next_sibling("a").get_text()[1:-1])
    data = dict()
    for input in form.select("input"):
        data[input["name"]] = input["value"]
    return (units, data)

def get_confirm_screen(session, domain, form, units, target_x, target_y, type):
    params = {"village": form["source_village"], "screen": "place", "try": "confirm"}

    payload = form.copy()
    if type == "attack":
        del payload["support"]
    else:
        del payload["attack"]
    payload["x"] = target_x
    payload["y"] = target_y
    for unit in units:
        payload[unit] = units[unit]

    response = session.post("https://" + domain + "/game.php",
        params=params, data=payload)

    soup = BeautifulSoup(response.content, 'html.parser')
    error_box = soup.select("div[class=error_box]")
    if len(error_box) >= 1:
        error = error_box[0].get_text().strip()
        print(error)
        return None

    form = soup.select("form#command-data-form")[0]
    action = form["action"]
    data = dict()
    for input in form.select("input"):
        if "name" in input.attrs and "value" in input.attrs:
            data[input["name"]] = input["value"]
    return (action, data)

def just_do_it(session, domain, action, data):
    response = session.post("https://" + domain + action, data=data)

def intelli_single(format, actual):
    format = str(format)
    # Format: x
    match = re.fullmatch(r"[0-9]+", format)
    if match is not None:
        val = int(format)
        return min(val, actual)
    # Format: *
    if format == "*":
        return actual
    # Format: >=x
    match = re.fullmatch(r">=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        if actual >= requested:
            return actual
        else:
            return None
    # Format: =x
    match = re.fullmatch(r"=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        if actual >= requested:
            return requested
        else:
            return None
    # Format: -x
    match = re.fullmatch(r"-([0-9]+)", format)
    if match is not None:
        reduce = int(match.group(1))
        return max(actual - reduce, 0)
    # Error
    raise ValueError("Unknown format: {0}".format(format))

def get_local_offset():
    client = ntplib.NTPClient()
    response = client.request("europe.pool.ntp.org", version=3)
    return timedelta(seconds=response.offset)

def get_ping(domain):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    before = datetime.datetime.now()
    s.connect((domain, 80))
    after = datetime.datetime.now()
    s.close()
    return after - before

class SendActionThread(threading.Thread):
    def __init__(self, action):
        threading.Thread.__init__(self)
        self.action = action

    def run(self):
        keks_file = os.path.join(os.path.expanduser("~"), ".dstimer", "keks", self.action["domain"], self.action["player"])
        with open(keks_file) as fd:
            sid = fd.read()
        domain = self.action["domain"]

        with requests.Session() as session:
            session.cookies.set("sid", sid)
            session.headers.update({"user-agent": USER_AGENT})

            offset = get_local_offset()
            ping = get_ping(domain)
            print("Offset {0} seconds, Ping {1} ms".format(offset.total_seconds(), ping.total_seconds() * 1000))
            real_departure = dateutil.parser.parse(self.action["departure_time"]) - offset - ping

            while real_departure - datetime.datetime.now() > datetime.timedelta(seconds=3):
                time_left = real_departure - datetime.datetime.now() - datetime.timedelta(seconds=3)
                time.sleep((time_left / 2).total_seconds())

            print("Prepare job")
            (units, form) = get_place_screen(session, domain, self.action["source_id"])
            (action, data) = get_confirm_screen(session, domain, form, self.action["units"],
                self.action["target_coord"]["x"], self.action["target_coord"]["y"], self.action["type"])

            print("Wait for sending")
            while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=1):
                time_left = real_departure - datetime.datetime.now()
                time.sleep((time_left / 2).total_seconds())

            just_do_it(session, domain, action, data)
            print("Finished job")

def cycle():
    now = datetime.datetime.now()
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    trash_path = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    os.makedirs(schedule_path, exist_ok=True)
    os.makedirs(trash_path, exist_ok=True)

    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
            departure = dateutil.parser.parse(action["departure_time"])
            if departure - now < datetime.timedelta(seconds=65):
                # Move action file to trash folder
                os.rename(os.path.join(schedule_path, file), os.path.join(trash_path, file))
                # Execute the action in the near future
                print("Schedule action for {0}".format(departure))
                thread = SendActionThread(action)
                thread.start()

def main():
    while True:
        cycle()
        time.sleep(60)

if __name__ == "__main__":
    main()
