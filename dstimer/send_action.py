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
import re
from dstimer.intelli_unit import intelli_all, intelli_train
import dstimer.import_action
import dstimer.common as common
import dstimer.incomings_handler as incomings_handler
import random
from dstimer.import_keks import check_and_save_sids
from tcp_latency import measure_latency
from dstimer.models import Attacks
from dstimer import db
from flask import flash, Markup


logger = logging.getLogger("dstimer")


def check_reponse(response):
    if response.url.endswith("/sid_wrong.php"):
        raise ValueError("Session is invalid")


def get_place_screen(session, domain, village_id, vacation):
    params = dict(village=village_id, screen="place")
    if str(vacation) != "0":
        logger.info("vacation_mode")
        params["t"] = vacation
        headers = dict(referer="https://" + domain + "/game.php?t=" + str(vacation))
    else:
        headers = dict(referer="https://" + domain + "/game.php")
    response = session.get("https://" + domain + "/game.php", params=params, headers=headers)
    check_reponse(response)
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.find(id="command-data-form")
    units = dict()
    data = dict()
    for input in form.findAll("input", {"id": re.compile('unit_input_*')}):
        units[input["name"]] = int(input["data-all-count"])

    for input in form.findAll("input"):
        data[input["name"]] = input["value"]

    return (units, data, response.url)


def get_confirm_screen(session, domain, form, units, target_x, target_y, type, vacation, referer):
    building = common.read_options()["kata-target"]
    params = {"village": form["source_village"], "screen": "place", "try": "confirm"}
    if str(1) != "0":
        params["t"] = str(vacation)
    payload = form.copy()
    if type == "attack":
        del payload["support"]
    else:
        del payload["attack"]
    payload["x"] = str(target_x)
    payload["y"] = str(target_y)
    for unit in units:
        payload[unit] = units[unit]

    headers = dict(referer=referer)
    response = session.post("https://" + domain + "/game.php", params=params, data=payload,
                            headers=headers)
    check_reponse(response)

    soup = BeautifulSoup(response.content, 'html.parser')
    error = parse_after_send_error(soup)
    if error is not None:
        raise ValueError(error)

    form = soup.find(id="command-data-form")
    action = form["action"]
    data = dict()

    for input in form.findAll("input"):
        if "name" in input.attrs and "value" in input.attrs:
            data[input["name"]] = input["value"]
    try:
        building = form.find("option", selected=True)["value"]
    except:
        building = None
    return (building, action, data, response.url)


def just_do_it(session, domain, action, data, referer):
    headers = dict(referer=referer)
    response = session.post("https://" + domain + action, data=data, headers=headers)
    check_reponse(response)
    soup = BeautifulSoup(response.content, 'html.parser')
    error = parse_after_send_error(soup)
    if error is not None:
        raise ValueError(error)

def get_cancel_link(session, domain, village_id, attack_id):
    attack_name = "dst_cancel_" + str(attack_id)
    params = dict(village=village_id, screen="place")
    headers = dict(referer="https://" + domain + "/game.php")
    response = session.get("https://" + domain + "/game.php", params=params, headers=headers)
    check_reponse(response)
    soup = BeautifulSoup(response.content, 'html.parser')
    outgoings = soup.select("div#commands_outgoings")[0]
    found = False
    cancel_link = None
    for row in outgoings.select("tr.command-row"):
        for span in row.select("span.quickedit-label"):
            if span.text.strip() == attack_name:
                found = True
                break
        if found:
            cancel_link = row.select("a.command-cancel")[0]["href"]
    return (cancel_link, response.url)

def cancel_attack(session, domain, village_id, referer, params):
    logger.info("Canceling...")
    headers = dict(referer = referer)
    params["action"] = "cancel"
    response = session.get("https://" + domain + "/game.php", params=params, headers=headers)
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
        response = client.request("de.pool.ntp.org", version=3)
        return timedelta(seconds=response.offset)
    except:
        logger.info("Can't connect to 'de.pool.ntp.org'!")
        #response.offset = 0.0
        return timedelta(seconds=0.0)
    #return timedelta(seconds=response.offset)


def get_ping(domain):
    pingList = measure_latency(host=domain, runs=10, timeout=0.2)
    logger.debug("Ping List: " + str(pingList))
    if not list(filter(None, pingList)):
        logger.info("ping failed")
        pingList = measure_latency(host=domain, runs=5, timeout=1)
        logger.debug("Ping List retry: " + str(pingList))
    avgPing = sum(filter(None, pingList)) / len(list(filter(None, pingList)))
    logger.info("avg Ping: " + str(avgPing))
    return timedelta(microseconds=avgPing * 1000)


class SendActionThread(threading.Thread):

    def __init__(self, action, offset, ping, file = None):
        threading.Thread.__init__(self)
        self.action = action
        self.offset = offset
        self.ping = ping
        self.file = file

    def get_train_units(self):
        pending_path = os.path.join(common.get_root_folder(), "pending")
        next_attack = self.action["next_attack"]

        counter = 0
        while next_attack:
            for file in os.listdir(pending_path):
                if os.path.isfile(os.path.join(pending_path, file)) and next_attack in file:
                    with open(os.path.join(pending_path, file)) as fd:
                        a = json.load(fd)
                    for unit in a["units"]:
                        self.action["train[" + str(counter + 2) + "][" + unit + "]"] = str(
                            a["units"][unit])
                    next_attack = a["next_attack"]
                    counter += 1
                    break
        self.action["traincounter"] = counter

    def run(self):
        try:
            pending_path = os.path.join(common.get_root_folder(), "pending")
            failed_path = os.path.join(common.get_root_folder(), "failed")
            keks_path = os.path.join(common.get_root_folder(), "keks", self.action["domain"])
            if self.action["sitter"] == "0":
                keks_file = os.path.join(
                    keks_path,
                    self.action["player_id"] + "_" + common.filename_escape(self.action["player"]))
            else:
                for filename in os.listdir(keks_path):
                    if self.action["sitter"] in filename:
                        keks_file = os.path.join(keks_path, filename)
            with open(keks_file) as fd:
                sid = fd.read()
            domain = self.action["domain"]
            # Adding train units
            self.get_train_units()

            with requests.Session() as session:
                session.cookies.set("sid", sid)
                session.headers.update({"user-agent": common.USER_AGENT})
                real_departure = dateutil.parser.parse(
                    self.action["departure_time"]) - self.offset - self.ping

                while real_departure - datetime.datetime.now() > datetime.timedelta(seconds=5):
                    time_left = real_departure - datetime.datetime.now() - datetime.timedelta(
                        seconds=5)
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())

                logger.info("Prepare job. Forcing attack is " + str(self.action["force"]) + "!")
                if self.action["force"]:
                    #waiting till 100ms before departur.. reason: wait for troops to come back
                    logger.info("Wait for 100ms before!")
                    while real_departure - datetime.datetime.now() > datetime.timedelta(
                            milliseconds=100):
                        time_left = real_departure - datetime.datetime.now()
                        if time_left.total_seconds() <= 0:
                            break
                        time.sleep((time_left / 2).total_seconds())
                (actual_units, form, referer) = get_place_screen(session, domain,
                                                                 self.action["source_id"],
                                                                 self.action["vacation"])
                #for protecting troops from retimes...
                if self.action["force"]:
                    #if attack is forced, then no check vs. actual_units
                    units = self.action["units"]
                else:
                    logger.info("Checking for available units...")
                    units = intelli_all(self.action["units"], actual_units)
                if units is None:
                    raise ValueError(
                        "Could not satisfy unit conditions. Expected: {0}, Actual {1}".format(
                            self.action["units"], actual_units))

                if not intelli_train(self.action, actual_units):
                    raise ValueError("Could not satisfy combined unit conditions.")

                # Check if speed of troops has changed
                logger.info("Checking for change in unit speed...")
                stats = dstimer.import_action.get_cached_unit_info(domain)
                original_speed = dstimer.import_action.speed(self.action["units"],
                                                             self.action["type"], stats)
                current_speed = dstimer.import_action.speed(units, self.action["type"], stats)
                if original_speed != current_speed:
                    raise ValueError(
                        "Unit speed changed from {0} to {1} with units in village {2}, user format {3} and calculated {4}"
                        .format(original_speed, current_speed, actual_units, self.action["units"],
                                units))
                logger.info("Confirm.")

                (building, action, data, referer) = get_confirm_screen(
                    session, domain, form, units, self.action["target_coord"]["x"],
                    self.action["target_coord"]["y"], self.action["type"], self.action["vacation"],
                    referer)
                if building:
                    data["building"] = self.action[
                        "building"] if self.action["building"] != "default" else building
                    data["save_default_attack_building"] = self.action[
                        "save_default_attack_building"]

                for i in range(self.action["traincounter"]):
                    for unit in common.unitnames:
                        if "train[" + str(i + 2) + "][" + unit + "]" in self.action:
                            data["train[" + str(i + 2) + "][" + unit +
                                 "]"] = self.action["train[" + str(i + 2) + "][" + unit + "]"]

                logger.info("Wait for sending")
                while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=1):
                    time_left = real_departure - datetime.datetime.now()
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())

                logger.info("Time left: " + str(real_departure - datetime.datetime.now()))
                logger.info("data: " + json.dumps(data))
                just_do_it(session, domain, action, data, referer)
                logger.info("Finished job")
                # Delete finished action file
                os.remove(os.path.join(pending_path, self.file))
        except Exception as e:
            logger.error(str(e))
            # Move action file to failed folder
            os.rename(os.path.join(pending_path, self.file), os.path.join(failed_path, self.file))

class SendActionThread_DB(threading.Thread):
    def __init__(self, id, offset, ping):
        threading.Thread.__init__(self)
        self.id = id
        self.offset = offset
        self.ping = ping
        attack = Attacks.query.filter_by(id = id).first()
        self.action = attack.load_action()
        attack.status = "pending"
        db.session.add(attack)
        db.session.commit()
    
    def run(self):
        try:
            keks_path = os.path.join(common.get_root_folder(), "keks", self.action["domain"])
            keks_file = os.path.join(
                keks_path,
                str(self.action["player_id"]) + "_" + common.filename_escape(self.action["player"]))
            with open(keks_file) as fd:
                sid = fd.read()
            domain = self.action["domain"]
            real_departure = self.action["departure_time"] - self.offset - self.ping

            with requests.Session() as session:
                session.cookies.set("sid", sid)
                session.headers.update({"user-agent": common.USER_AGENT})

                while real_departure - datetime.datetime.now() > datetime.timedelta(seconds=5):
                    time_left = real_departure - datetime.datetime.now() - datetime.timedelta(
                        seconds=5)
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())
                logger.info("Prepare job. Forcing attack is " + str(self.action["force"]) + "!")
                (actual_units, form, referer) = get_place_screen(session, domain,
                                                                 self.action["source_id"],
                                                                 self.action["vacation"])
                                                                 
                logger.info("Checking for available units...")
                units = intelli_all(self.action["units"], actual_units)
                if units is None:
                    raise ValueError(
                        "Could not satisfy unit conditions. Expected: {0}, Actual {1}".format(
                            self.action["units"], actual_units))
                
                # Check if speed of troops has changed
                logger.info("Checking for change in unit speed...")
                stats = dstimer.import_action.get_cached_unit_info(domain)
                original_speed = dstimer.import_action.speed(self.action["units"],
                                                             self.action["type"], stats)
                current_speed = dstimer.import_action.speed(units, self.action["type"], stats)
                if original_speed != current_speed and not self.action["cancel_time"]:
                    raise ValueError(
                        "Unit speed changed from {0} to {1} with units in village {2}, user format {3} and calculated {4}"
                        .format(original_speed, current_speed, actual_units, self.action["units"],
                                units))
                logger.info("Confirm.")

                (building, action, data, referer) = get_confirm_screen(
                    session, domain, form, units, self.action["target_coord"]["x"],
                    self.action["target_coord"]["y"], self.action["type"], self.action["vacation"],
                    referer)
                if building:
                    data["building"] = self.action[
                        "building"] if self.action["building"] != "default" else building
                    data["save_default_attack_building"] = self.action[
                        "save_default_attack_building"]
                                           
                if self.action["cancel_time"]:
                    data["attack_name"] = "dst_cancel_" + str(self.action["id"])
                    logger.info("Renaming attack to {}. Cancel Time is {}.".format(data["attack_name"], self.action["cancel_time"]))

                logger.info("Wait for sending")
                while real_departure - datetime.datetime.now() > datetime.timedelta(milliseconds=1):
                    time_left = real_departure - datetime.datetime.now()
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())
                
                logger.info("Time left: " + str(real_departure - datetime.datetime.now()))
                logger.info("data: " + json.dumps(data))
                just_do_it(session, domain, action, data, referer)
                logger.info("Finished job")

                attack = Attacks.query.filter_by(id = self.id).first()
                if attack.cancel_time:
                    attack.status = "cancel"
                    thread = CancelActionThread(attack.id, self.offset, self.ping)
                    thread.start()
                else:
                    attack.status = "finished"
                db.session.add(attack)
                db.session.commit()

        except Exception as e:
            logger.error(str(e))
            attack = Attacks.query.filter_by(id = self.id).first()
            attack.status = "failed"
            db.session.add(attack)
            db.session.commit()

class CancelActionThread(threading.Thread):
    def __init__(self, id, offset, ping):
        threading.Thread.__init__(self)
        self.id = id
        self.offset = offset
        self.ping = ping
        attack = Attacks.query.filter_by(id = id).first()
        self.action = attack.load_action()
    
    def run(self):
        try:
            attack = Attacks.query.filter_by(id = self.id).first()
            real_cancel_time = self.action["cancel_time"] - self.offset - self.ping
            with requests.Session() as session:
                session.cookies.set("sid", attack.player.sid)
                session.headers.update({"user-agent": common.USER_AGENT})

                while real_cancel_time - datetime.datetime.now() > datetime.timedelta(seconds=5):
                    time_left = real_cancel_time - datetime.datetime.now() - datetime.timedelta(
                        seconds=5)
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())
                
                logger.info("Preparing cancelation.")
                (cancel_link, referer) = get_cancel_link(session, attack.player.domain, attack.source_id, attack.id)

                params = dict()
                params["village"] = attack.source_id
                params["screen"] = "place"
                params["id"] = cancel_link.split("id=")[1].split("&")[0]
                params["h"] = cancel_link.split("h=")[1].split("&")[0]

                while real_cancel_time - datetime.datetime.now() > datetime.timedelta(milliseconds=1):
                    time_left = real_cancel_time - datetime.datetime.now()
                    if time_left.total_seconds() <= 0:
                        break
                    time.sleep((time_left / 2).total_seconds())

                logger.info("Time left: " + str(real_cancel_time - datetime.datetime.now()))


                cancel_attack(session, attack.player.domain, attack.source_id, referer, params)
                logger.info("canceling finished at: {}".format(datetime.datetime.now()))

                attack.status = "finished"
                db.session.add(attack)
                db.session.commit()

        except Exception as e:
            logger.error(str(e))
            message = Markup("Cancel evacuation failed! Visit ")
            flash(message)
            attack = Attacks.query.filter_by(id = self.id).first()
            attack.status = "failed"
            message = Markup("Cancel evacuation failed! Visit <a href='" + attack.player.domain + "/game.php?village=" + attack.source_id + "screen=place'>this link</a>.")
            flash(message)
            db.session.add(attack)
            db.session.commit()

def cycle():
    now = datetime.datetime.now()
    schedule_path = os.path.join(common.get_root_folder(), "schedule")
    pending_path = os.path.join(common.get_root_folder(), "pending")
    expired_path = os.path.join(common.get_root_folder(), "expired")

    offset = None
    ping = {}
    train_ignore = []

    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
            # train
            if action["next_attack"]:
                train_ignore.append(action["next_attack"])
            if file.split("_")[1].split(".")[0] in train_ignore:
                #logger.info("skipping")
                continue
            #else:
            #logger.info("not skipping")
            departure = dateutil.parser.parse(action["departure_time"])
            if departure < now:
                logger.error(
                    "Action scheduled for {0} is expired. Will not send.".format(departure))
                # Move action file to expired folder
                os.rename(os.path.join(schedule_path, file), os.path.join(expired_path, file))
            elif departure - now < datetime.timedelta(seconds=90):
                # Move action file to pending folder
                os.rename(os.path.join(schedule_path, file), os.path.join(pending_path, file))
                # Moving all scheduled actions of a train to pending folder
                next_attack = action["next_attack"]
                while next_attack:
                    for file in os.listdir(schedule_path):
                        if os.path.isfile(os.path.join(schedule_path,
                                                       file)) and next_attack in file:
                            with open(os.path.join(schedule_path, file)) as fd:
                                a = json.load(fd)
                            os.rename(os.path.join(schedule_path, file),
                                      os.path.join(pending_path, file))
                            next_attack = a["next_attack"]
                            break
                # Request Offset & Ping
                domain = action["domain"]
                if offset is None:
                    offset = get_local_offset()
                    logger.info("Time Offset: {0} ms".format(round(offset.total_seconds() * 1000)))
                if domain not in ping:
                    ping[domain] = get_ping(domain)
                    logger.info("Ping for {0}: {1} ms".format(domain,
                                                              ping[domain].total_seconds() * 1000))

                # Execute the action in the near future
                logger.info("Schedule action for {0}".format(departure))
                thread = SendActionThread(action, offset, ping[domain], file)
                thread.start()

def cycle_db():
    attacks = Attacks.query.filter_by(status = "scheduled").all()
    now = datetime.datetime.now()
    ping = dict()
    offset = None
    for attack in attacks:
        action = attack.load_action()
        departure = action["departure_time"]
        if departure < now:
            logger.error("Action scheduled for {0} is expired. Will not send.".format(departure))
            attack.status = "expired"
            db.session.add(attack)
            db.session.commit()
        elif departure - now < datetime.timedelta(seconds=90):
            domain = action["domain"]
            if offset is None:
                offset = get_local_offset()
                logger.info("Time Offset: {0} ms".format(round(offset.total_seconds() * 1000)))
            if domain not in ping:
                ping[domain] = get_ping(domain)
                logger.info("Ping for {0}: {1} ms".format(domain, ping[domain].total_seconds() * 1000))
            logger.info("Schedule action for {0}".format(departure))
            #attack.status = "pending"
            #db.session.add(attack)
            #db.session.commit()           
            thread = SendActionThread_DB(attack.id, offset, ping[domain])
            thread.start()


class DaemonThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        print("Daemon is running")
        check_sid_counter = 0
        while True:
            try:
                cycle_db()
            except Exception as e:
                logger.warning(e)
            if check_sid_counter == 0:
                check_and_save_sids()
                check_sid_counter = random.randint(30, 90)    # every 30 to 90 minutes
            else:
                check_sid_counter -= 1
            time.sleep(30)
