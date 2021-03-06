import requests
import json
import os
import re
from datetime import datetime
from dstimer import common
from bs4 import BeautifulSoup
import logging
from dstimer.models import Player, Group
from dstimer import world_data, db


logger = logging.getLogger("dstimer")
FORMAT = re.compile(r"\[([a-zA-Z\.\-0-9]+)\|([a-zA-Z0-9%:]+)\|([a-zA-Z0-9]{8})\]")


def parse_keks(str):
    """Parse an exported session cookie string from DS Kekse."""
    match = FORMAT.search(str)
    if match:
        return dict(domain=match.group(1), sid=match.group(2))
    else:
        return None


def player_id_from_keks(keks):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": common.USER_AGENT}
    response = requests.get("https://" + keks["domain"] + "/game.php", cookies=cookies,
                            headers=headers)    #, verify=False)
    for line in response.content.decode("utf-8").splitlines():
        if line.strip().startswith("TribalWars.updateGameData("):
            game_data = json.loads(line[line.index("(") + 1:line.rindex(")")])
            return (game_data["player"]["id"], game_data["player"]["name"])
    return None, None


def write_keks(keks, id, name):
    directory = os.path.join(common.get_root_folder(), "keks", keks["domain"])
    name_clean = common.filename_escape(name)
    filename = id + "_" + name_clean
    file = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    with open(file, "w") as fd:
        fd.write(keks["sid"])

def write_keks_db(keks, id, name):
    player = Player.query.filter_by(player_id = id, domain = keks["domain"]).first()
    if player:
        player.sid = keks["sid"]
        player.sid_datetime = datetime.now()
    else:
        player = Player(
            name = name,
            player_id = id,
            sid = keks["sid"],
            sid_datetime = datetime.now(), 
            domain = keks["domain"]
        )
        all_group = Group(
            name = "Alle",
            group_id = 0, 
            is_used = True, 
            priority = 1,
            player = player
        )
        db.session.add(all_group)
    db.session.add(player)
    db.session.commit()
    

def import_from_text(text):
    keks = parse_keks(text)
    if keks is None:
        raise ValueError("Invalid keks: {0}".format(text))
    (id, name) = player_id_from_keks(keks)
    if id is None:
        raise ValueError("Session is expired or invalid")
    write_keks(keks, id, name)
    write_keks_db(keks, id, name)
    world_data.refresh_world_data()
    common.send_stats(common.create_stats(player_id=id, domain=keks["domain"]))


def check_sids():
    schedule_path = os.path.join(common.get_root_folder(), "schedule")
    players_to_check = set()
    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
            players_to_check.add((action["domain"], action["player"], action["player_id"]))

    issues = []
    for (domain, player, player_id) in players_to_check:
        player_clean = "".join(i for i in player if i.isalnum())
        keks_file = os.path.join(common.get_root_folder(), "keks", domain,
                                 player_id + "_" + common.filename_escape(player_clean))
        try:
            with open(keks_file) as fd:
                sid = fd.read()
        except:
            issues.append(dict(domain=domain, player=player, issue="notfound"))
            continue
        response = requests.get("https://" + domain + "/game.php", cookies=dict(sid=sid),
                                headers={"user-agent": common.USER_AGENT})
        if response.url.endswith("/sid_wrong.php"):
            issues.append(dict(domain=domain, player=player, issue="invalid"))
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        if len(soup.select("div#bot_check")) >= 1:
            issues.append(dict(domain=domain, player=player, issue="botcheck"))
    return issues


def check_and_save_sids():
    issues = check_sids()
    #    logger.info()
    with open(os.path.join(common.get_root_folder(), "status.txt"), "w") as fd:
        json.dump(issues, fd)
