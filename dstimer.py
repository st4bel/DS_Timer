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

def get_place_screen(keks, village_id):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": USER_AGENT}
    params = dict(village=village_id, screen="place")
    response = requests.get("https://" + keks["domain"] + "/game.php", params=params, cookies=cookies, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.select("form#command-data-form")[0]
    units = dict()
    for input in form.select("input[id^=unit_input_]"):
        units[input["name"]] = int(input.find_next_sibling("a").get_text()[1:-1])
    data = dict()
    for input in form.select("input"):
        data[input["name"]] = input["value"]

    return (units, data)

def get_confirm_screen(keks, form, units, target_x, target_y, type):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": USER_AGENT}
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

    response = requests.post("https://" + keks["domain"] + "/game.php",
        params=params, cookies=cookies, headers=headers, data=payload)

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

def just_do_it(keks, action, data):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": USER_AGENT}
    response = requests.post("https://" + keks["domain"] + action,
        cookies=cookies, headers=headers, data=data)

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
        print(action)

    def run(self):
        keks_file = os.path.join(os.path.expanduser("~"), ".dstimer", "keks", self.action["domain"], self.action["player"])
        with open(keks_file) as fd:
            sid = fd.read()
        keks = dict(domain=self.action["domain"], sid=sid)

        (units, form) = get_place_screen(keks, self.action["source_id"])
        (action, data) = get_confirm_screen(keks, form, self.action["units"],
            self.action["target_coord"]["x"], self.action["target_coord"]["y"], self.action["type"])

        offset = get_local_offset()
        ping = get_ping(keks["domain"])
        print("Offset {0} Ping {1}".format(offset, ping))
        real_departure = dateutil.parser.parse(self.action["departure_time"]) - offset - ping

        print(real_departure)

        while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=5):
            time_left = real_departure - datetime.datetime.now()
            print(time_left)
            time.sleep((time_left / 2).total_seconds())

        print(datetime.datetime.now())
        just_do_it(keks, action, data)
        print(datetime.datetime.now())

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
            print("departure {0}".format(departure))
            print("now {0}".format(now))
            if departure - now < datetime.timedelta(seconds=90):
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
