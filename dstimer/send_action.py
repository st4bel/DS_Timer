#!/usr/bin/env python3
import time
import dateutil.parser
import datetime
import json
import requests
from bs4 import BeautifulSoup
import math
import xml.etree.ElementTree as ET
from datetime import timedelta
import ntplib
import threading
import os
import json
import socket
import logging
from dstimer.intelli_unit import intelli_all
import dstimer.import_action
import dstimer.common as common
import random
from dstimer.import_keks import check_and_save_sids

logger = logging.getLogger("dstimer")

def check_reponse(response):
    if response.url.endswith("/sid_wrong.php"):
        raise ValueError("Session is invalid")

def get_place_screen(session, domain, village_id):
    params = dict(village=village_id, screen="place")
    headers = dict(referer="https://" + domain + "/game.php")
    response = session.get("https://" + domain + "/game.php", params=params, headers=headers)
    check_reponse(response)
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.select("form#command-data-form")[0]
    units = dict()
    for input in form.select("input[id^=unit_input_]"):
        units[input["name"]] = int(input.find_next_sibling("a").get_text()[1:-1])
    data = dict()
    for input in form.select("input"):
        data[input["name"]] = input["value"]
    return (units, data, response.url)

def get_confirm_screen(session, domain, form, units, target_x, target_y, type, referer):
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

    headers = dict(referer=referer)
    response = session.post("https://" + domain + "/game.php",
        params=params, data=payload, headers=headers)
    check_reponse(response)

    soup = BeautifulSoup(response.content, 'html.parser')
    error = parse_after_send_error(soup)
    if error is not None:
        raise ValueError(error)

    form = soup.select("form#command-data-form")[0]
    action = form["action"]
    data = dict()
    for input in form.select("input"):
        if "name" in input.attrs and "value" in input.attrs:
            data[input["name"]] = input["value"]
    return (action, data, response.url)

def just_do_it(session, domain, action, data, referer):
    headers = dict(referer=referer)
    response = session.post("https://" + domain + action, data=data, headers=headers)
    check_reponse(response)
    soup = BeautifulSoup(response.content, 'html.parser')
    error = parse_after_send_error(soup)
    if error is not None:
        raise ValueError(error)

def parse_after_send_error(soup):
    error_box = soup.select("div[class=error_box]")
    if len(error_box) >= 1:
        return error_box[0].get_text().strip()
    return None

def get_local_offset():
    try:
        client = ntplib.NTPClient()
        response = client.request("europe.pool.ntp.org", version=3)
        return timedelta(seconds=response.offset)
    except:
        response.offset = 0.0
        return timedelta(seconds = 0.0)
    #return timedelta(seconds=response.offset)

def get_ping(domain):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    before = datetime.datetime.now()
    s.connect((domain, 80))
    after = datetime.datetime.now()
    s.close()
    return after - before

class SendActionThread(threading.Thread):
    def __init__(self, action, offset, ping, file):
        threading.Thread.__init__(self)
        self.action = action
        self.offset = offset
        self.ping = ping
        self.file = file

    def run(self):
        try:
            pending_path = os.path.join(common.get_root_folder(), "pending")
            failed_path = os.path.join(common.get_root_folder(), "failed")
            keks_file = os.path.join(common.get_root_folder(), "keks", self.action["domain"], self.action["player"])
            with open(keks_file) as fd:
                sid = fd.read()
            domain = self.action["domain"]

            with requests.Session() as session:
                session.cookies.set("sid", sid)
                session.headers.update({"user-agent": common.USER_AGENT})

                real_departure = dateutil.parser.parse(self.action["departure_time"]) - self.offset - self.ping

                while real_departure - datetime.datetime.now() > datetime.timedelta(seconds=5):
                    time_left = real_departure - datetime.datetime.now() - datetime.timedelta(seconds=5)
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())

                logger.info("Prepare job")
                if self.action["force"]:
                    #waiting till 100ms before departur.. reason: wait for troops to come back
                    logger.info("Wait for 100ms before!")
                    while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=100):
                        time_left = real_departure - datetime.datetime.now()
                        if time_left.total_seconds() <= 0:
                            break
                        time.sleep((time_left / 2).total_seconds())
                (actual_units, form, referer) = get_place_screen(session, domain, self.action["source_id"])
                #for protecting troops from retimes...
                if self.action["force"]:
                    #if force, then no check vs. actual_units
                    units = self.action["units"]
                else:
                    units = intelli_all(self.action["units"], actual_units)
                if units is None:
                    raise ValueError("Could not satisfy unit conditions. Expected: {0}, Actual {1}".format(
                        self.action["units"], actual_units))

                # Check if speed of troops has changed
                stats = dstimer.import_action.get_cached_unit_info(domain)
                original_speed = dstimer.import_action.speed(self.action["units"], self.action["type"], stats)
                current_speed = dstimer.import_action.speed(units, self.action["type"], stats)
                if original_speed != current_speed:
                    raise ValueError("Unit speed changed from {0} to {1} with units in village {2}, user format {3} and calculated {4}".format(
                        original_speed, current_speed, actual_units, self.action["units"], units))

                (action, data, referer) = get_confirm_screen(session, domain, form, units,
                    self.action["target_coord"]["x"], self.action["target_coord"]["y"], self.action["type"], referer)

                logger.info("Wait for sending")
                while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=1):
                    time_left = real_departure - datetime.datetime.now()
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())
                logger.info("Time left: "+str(real_departure - datetime.datetime.now()))
                just_do_it(session, domain, action, data, referer)
                logger.info("Finished job")
                # Delete finished action file
                os.remove(os.path.join(pending_path, self.file))
        except Exception as e:
            logger.error(str(e))
            # Move action file to failed folder
            os.rename(os.path.join(pending_path, self.file), os.path.join(failed_path, self.file))

def cycle():
    now = datetime.datetime.now()
    schedule_path = os.path.join(common.get_root_folder(), "schedule")
    pending_path = os.path.join(common.get_root_folder(), "pending")
    expired_path = os.path.join(common.get_root_folder(), "expired")

    offset = None
    ping = {}

    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
            departure = dateutil.parser.parse(action["departure_time"])
            if departure < now:
                logger.error("Action scheduled for {0} is expired. Will not send.".format(departure))
                # Move action file to expired folder
                os.rename(os.path.join(schedule_path, file), os.path.join(expired_path, file))
            elif departure - now < datetime.timedelta(seconds=90):
                # Move action file to pending folder
                os.rename(os.path.join(schedule_path, file), os.path.join(pending_path, file))
                # Request Offset & Ping
                domain = action["domain"]
                if offset is None:
                    offset = get_local_offset()
                    logger.info("Time Offset: {0} ms".format(round(offset.total_seconds() * 1000)))
                if domain not in ping:
                    ping[domain] = get_ping(domain)
                    logger.info("Ping for {0}: {1} ms".format(domain, round(ping[domain].total_seconds() * 1000)))
                # Execute the action in the near future
                logger.info("Schedule action for {0}".format(departure))
                thread = SendActionThread(action, offset, ping[domain], file)
                thread.start()

class DaemonThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        print("Daemon is running")
        check_sid_counter = 0
        while True:
            cycle()
            if check_sid_counter == 0:
                check_and_save_sids()
                check_sid_counter = random.randint(30, 90) # every 30 to 90 minutes
            else:
                check_sid_counter -= 1
            time.sleep(60)
