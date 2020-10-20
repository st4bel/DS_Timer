import os
import dstimer.common as common
import requests
from bs4 import BeautifulSoup
import logging
from dstimer import common, world_data
from dstimer.models import *
from dstimer import db
from sqlalchemy.exc import IntegrityError

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
    # return template id or None, if all cases are ignored
    inc = Incomings.query.filter_by(inc_id=inc_id).first()
    # gruppen des Zieldorfes laden, nach priorität sortieren
    groups = sorted(inc.village.groups(), key=lambda group: group.priority)

    # get inctype by priority (in this case its my preconceived priority)
    if (inc.unit_symbol is "snob") or (inc.slowest_unit is "snob"):
        inctype_name = "snob"
    elif (inc.unit_symbol is "spy") or (inc.slowest_unit is "spy"):
        inctype_name = "spy"
    else:
        inctype_name = inc.size
    inctype = Inctype.query.filter_by(name = inctype_name).first()

    template_id = None # if in all cases ignored
    # looping over groups by priority to find first non ignored template
    for group in groups:
        e = Evacoption.query.filter_by(group = group, inctype = inctype).first()
        if e.is_ignored:
            continue
        template_id = e.template.id
    
    return template_id

def group_incs(domain, player_id):
    # grouping incs which reach the same village in quick succession.
    player = Player.query.filter_by(player_id=player_id, domain=domain).first()
    #incs = Incomings.query.filter_by(player=player).order_by("arrival_time").all()
    villages = Village.query.filter_by(player=player)

    # villages with more than 1 inc:
    mult_inc_vill = [v for v in villages if len(v.incs.all()) > 1]
    for village in mult_inc_vill:
        incs = Incomings.query.filter_by(village = village).order_by("arrival_time").all()
        for i in range(len(incs)-1):
            # cycling through incs checking if diff in arrival time is smaller than threshold
            diff = incs[i].arrival_time - incs[i+1].arrival_time
            # TODO: what if ignored incs are between?, what if different templates would be used

    return

def cycle():
    return