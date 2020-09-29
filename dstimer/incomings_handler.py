import os
import dstimer.common as common
import requests
from bs4 import BeautifulSoup
import logging
from dstimer import common
from dstimer.models import Incomings
from dstimer import db
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("dstimer")

def check_reponse(response):
    if response.url.endswith("/sid_wrong.php"):
        raise ValueError("Session is invalid")

def load_incomings(domain, player, player_id):
    keks_path = os.path.join(common.get_root_folder(), "keks", domain)
    keks_file = os.path.join(keks_path, player_id + "_" + common.filename_escape(player))
    with open(keks_file) as fd:
        sid = fd.read()
    with requests.Session() as session:
        session.cookies.set("sid", sid)
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

            incomings[id] = inc
        
        # reset current group
        params = dict(screen = "overview_villages", mode = "incomings", subtype = "attacks", group = current_group_id)
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)


        return incomings
    return dict()

def save_current_incs(incs):
    # saves incs (dict) into database, checks if already saved
    for inc_id in incs:
        inc = incs[inc_id]
        a = Incomings(
            inc_id = int(inc["id"]),
            name = inc["name"],
            target_village_id = int(inc["target_village_id"]),
            target_village_name = inc["target_village_name"],
            source_village_id = int(inc["source_village_id"]),
            source_village_name = inc["source_village_name"],
            source_player_id = int(inc["source_player_id"]),
            source_player_name = inc["source_player_name"],
            distance = float(inc["distance"]),
            arrival_time = inc["arrival_time"]
        )
        db.session.add(a)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback() #  if inc already in db
