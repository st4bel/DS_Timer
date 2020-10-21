import os
import dstimer.common as common
import requests
from bs4 import BeautifulSoup
import logging
from dstimer import common, world_data
from dstimer.models import *
from dstimer import db
from sqlalchemy.exc import IntegrityError
import threading
import time
from datetime import datetime, timedelta

logger = logging.getLogger("dstimer")

def check_reponse(response):
    if response.url.endswith("/sid_wrong.php"):
        raise ValueError("Session is invalid")

def load_incomings(domain, player_id):
    player = Player.query.filter_by(domain=domain, player_id=player_id).first()
    with requests.Session() as session:
        session.cookies.set("sid", player.sid)
        session.headers.update({"user-agent": common.USER_AGENT})

        params = dict(screen = "overview_villages", mode = "incomings", subtype = "attacks")
        headers = dict(referer = "https://" + domain + "/game.php")

        response1 = session.get("https://" + domain + "/game.php", params=params, headers = headers)
        check_reponse(response1)

        soup1 = BeautifulSoup(response1.content, "html.parser")
                
        # getting current group id, load incomings under group "0" (alle), then again load the page under current group to not reset the group selected ingame
        current_group_id = soup1.select("strong.group-menu-item")[0]["data-group-id"]
        logger.info(current_group_id)
        params = dict(screen = "overview_villages", mode = "incomings", subtype = "attacks", group = "0")
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)
        check_reponse(response)

        soup = BeautifulSoup(response.content, "html.parser")

        if not soup.select("table#incomings_table"):
            logger.info("no incomings")
            return dict()

        table = soup.select("table#incomings_table")[0]

        incomings = dict()
        for row in table.select("tr.nowrap"):
            id = row.select("span.quickedit")[0]["data-id"]
            logger.info("inc_id: "+id)

            inc = dict()
            inc["id"] = id
            inc["name"] = row.select("td")[0].select("a")[0].text.strip()
            
            inc["target_village_id"] = int(row.select("td")[1].select("a")[0]["href"].split("village=")[1].split("&")[0])
            inc["target_village_name"] = row.select("td")[1].select("a")[0].text.strip()
            #logger.info(inc["target_village_name"])
            inc["source_village_id"] = int(row.select("td")[2].select("a")[0]["href"].split("id=")[1])
            inc["source_village_name"] = row.select("td")[2].select("a")[0].text.strip()
            inc["source_player_id"] = int(row.select("td")[3].select("a")[0]["href"].split("id=")[1])
            inc["source_player_name"] = row.select("td")[3].select("a")[0].text.strip()

            inc["distance"] = row.select("td")[4].text.strip()
            inc["arrival_string"] = row.select("td")[5].text.strip()
            inc["arrival_time"] = common.parse_timestring(row.select("td")[5].text)

            # get attack size and possibly detected unit
            images_src = [images["src"] for images in row.select("td")[0].select("img")]
            for src in images_src:
                if "attack" in src:
                    if len(src.split("attack_")) == 2:
                        inc["size"] = src.split("attack_")[1].split(".png")[0]
                    else:
                        inc["size"] = "default"
                elif ("spy" in src) or ("snob" in src):
                    inc["unit"] = src.split("command/")[1].split(".png")[0]
            
            incomings[id] = inc
        
        # reset current group
        params = dict(screen = "overview_villages", mode = "incomings", subtype = "attacks", group = current_group_id)
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)


        return incomings
    return dict()

def save_current_incs(incs, domain, player_id):
    # saves incs (dict) into database, checks if already saved
    player = Player.query.filter_by(player_id=player_id, domain = domain).first()
    player.refresh_groups()
    player.refresh_villages()
    for inc_id in incs:
        inc = incs[inc_id]
        if int(inc_id) not in [i.inc_id for i in Incomings.query.all()]:
            village = player.villages.filter_by(village_id = int(inc["target_village_id"])).first()
            if not village: # if villages have not been refreshed yet
                player.refresh_groups(1)
                player.refresh_villages(1)
                village = player.villages.filter_by(village_id = int(inc["target_village_id"])).first()
            i = Incomings(
                inc_id = int(inc["id"]),
                name = inc["name"],
                target_village_id = int(inc["target_village_id"]),
                target_village_name = inc["target_village_name"],
                source_village_id = int(inc["source_village_id"]),
                source_village_name = inc["source_village_name"],
                source_player_id = int(inc["source_player_id"]),
                source_player_name = inc["source_player_name"],
                distance = float(inc["distance"]),
                arrival_time = inc["arrival_time"],
                player = player,
                village = village
            )
        else:
            i = Incomings.query.filter_by(inc_id = int(inc_id)).first()
            i.name = inc["name"]
        
        if "size" in inc: #TODO Überprüfen, unter welchen bedingungen size und unit geändert werden darf
            i.size = inc["size"]
        else:
            i.size = "default"
        if "unit" in inc:
            i.unit_symbol = inc["unit"]
        else:
            i.unit_symbol = None
        if not i.slowest_unit:
            i.slowest_unit = i.get_slowest_unit()
        
        db.session.add(i)
    db.session.commit()

def cleanup_incs(current_incs, domain, player_id):
    # removes expired incs; checks if non expired incs do not anymore (e.g. canceled or village lost) 
    player = Player.query.filter_by(player_id=player_id, domain = domain).first()
    incs = Incomings.query.filter_by(player=player).all()
    warnings = []
    for inc in incs:
        if str(inc.inc_id) not in current_incs:
            db.session.delete(inc)
            warnings.append("Inc mit id {} nicht gefunden.".format(inc.inc_id))

    db.session.commit()
    return warnings

def decide_template(inc_id):
    # return template id (or None, if all cases are ignored), also return Inctype id
    inc = Incomings.query.filter_by(inc_id=inc_id).first()
    # gruppen des Zieldorfes laden, nach priorität sortieren
    groups = sorted(inc.village.groups, key=lambda g: g.priority)

    # get inctype by priority (in this case its my preconceived priority)
    if (inc.unit_symbol == "snob") or (inc.slowest_unit == "snob"):
        inctype_name = "snob"
    elif (inc.unit_symbol == "spy") or (inc.slowest_unit == "spy"):
        inctype_name = "spy"
    else:
        inctype_name = inc.size
    inctype = Inctype.query.filter_by(name = inctype_name).first()

    template_id = None # if in all cases ignored
    # looping over groups by priority to find first non ignored template
    for group in groups:
        e = Evacoption.query.filter_by(group = group, inctype = inctype).first()
        if not e.is_ignored:
            template_id = e.template.id
            break
    
    return dict(template_id = template_id, inctype_id = inctype.id)

def decide_group_template(inc_id):
    # if any template is None (ignored) than ignore all; if all are set, get template from highest priority inctype
    inc = Incomings.query.filter_by(inc_id=inc_id).first()
    if inc.previous_inc.first():
        return inc.previous_inc.first().template

    inc_group = [inc] + [i for i in inc.next_incs.order_by("arrival_time").all()]
    a = [decide_template(i.inc_id) for i in inc_group]

    if None in [b["template_id"] for b in a]:
        return None 
    
    # sorting "a" by argument "inctype_id", returning the template of first entry
    return sorted(a, key=lambda b: b["inctype_id"])[0]["template_id"]

def group_incs(domain, player_id):
    # grouping incs which reach the same village in quick succession. Does not decide, which template should be used
    player = Player.query.filter_by(player_id=player_id, domain=domain).first()
    villages = Village.query.filter_by(player=player)

    # villages with more than 1 inc:
    mult_inc_vill = [v for v in villages if len(v.incs.all()) > 1]
    for village in mult_inc_vill:
        incs = Incomings.query.filter_by(village = village).order_by("arrival_time").all()
        for i in range(len(incs)-1):
            # cycling through incs checking if diff in arrival time is smaller than threshold
            diff = incs[i+1].arrival_time - incs[i].arrival_time
            if diff > common.get_grouping_timedelta():
                continue
                
            # check, if incs[i] is already grouped; previous_inc points to the first inc
            if incs[i].previous_inc.first():
                incs[i].previous_inc.first().add_next_inc(incs[i+1])
            else:
                incs[i].add_next_inc(incs[i+1])
            
            db.session.add(incs[i+1])
    db.session.commit()

def plan_evac_action(inc_id):
    inc = Incomings.query.filter_by(inc_id=inc_id).first()
    a = Attacks()
    options = common.read_options()
    mill = 500
    # TODO: randomize departure and arrival time
    a.departure_time = (inc.arrival_time - timedelta(seconds=options["evac_pre_buffer_seconds"])).replace(microsecond=mill*1000)
    a.arrival_time = ((inc.arrival_time if len(inc.next_incs.all()) == 0 else inc.next_incs.order_by("arrival_time").all()[-1].arrival_time) + timedelta(seconds=options["evac_pre_buffer_seconds"])).replace(microsecond=mill*1000)
    runtime = a.arrival_time - a.departure_time
    a.cancel_time = a.departure_time + runtime/2 + timedelta(microsecond=100*1000) # problem if cancel time on microseconds = 0 (?)

    a.source_id = inc.village.village_id
    a.target_id = get_target_id(inc)
    a.player = inc.player
    a.units = inc.template.units
    a.force = False
    a.type = "attack"
    a.status = "scheduled"

    a.autocomplete()

    logger.info("Evacutation planned for village {} starting {}, canceling {}, returning {}".format(inc.village.get_village_name(), a.departure_time, a.cancel_time, a.arrival_time))

    db.session.add(a)
    db.session.commit()

def get_target_id(inc):
    # TODO: auswahl durch benutzer -> festes dorf, nächstes BB, "zufälliges" Eigenens, wenn ags: distance überprüfen
    v = Village.query.filter_by(player = inc.player).all()

    if v[0] is not inc.village:
        return v[0].village_id
    elif len(v) != 1:
        return v[1].village_id
    else: # if only one village, evac attack is send to attacker
        return inc.source_village_id




def cycle():
    players = Player.query.all()
    for player in players:
        if not player.is_active():
            continue
        loaded_incs = load_incomings(player.domain, player.player_id)
        save_current_incs(loaded_incs, player.domain, player.player_id)
        warnings = cleanup_incs(loaded_incs, player.domain, player.player_id)
        group_incs(player.domain, player.player_id)

        incs = incs = Incomings.query.filter_by(player = player).order_by("arrival_time").all()
        # setting template
        for inc in incs:
            template_id = decide_group_template(inc.inc_id)
            inc.template = Template.query.filter_by(id=template_id).first()
            db.session.add(inc)
        db.session.commit()

        now= datetime.now()
        # check, if evacuation is imminent
        for inc in incs:
            if inc.is_expired():
                db.session.remove(inc)
                db.session.commit()
                continue
            if inc.arrival_time - now < timedelta(minutes = 5):
                if inc.status == "pending" or not inc.template:
                    continue    
                inc.status = "pending"
                db.session.add(inc)
                db.session.commit()
                if inc.previous_inc.first():
                    if inc.previous_inc.first().status == "pending":
                        continue
                logger.info("Planing Evacutaion for {}. Template {}".format(inc.inc_id, inc.template.name))
                plan_evac_action(inc.inc_id)
            else:
                break # all other incs are further in the future

class DaemonThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        print("Evacuate_Daemon is running")
        while True:
            cycle()
            time.sleep(120)