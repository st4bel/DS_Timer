import requests
import json
import os
import re
from dstimer import common
from bs4 import BeautifulSoup
import logging
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
    response = requests.get("https://" +  keks["domain"] + "/game.php",
        cookies=cookies, headers=headers)#, verify=False)
    for line in response.content.decode("utf-8").splitlines():
        if line.strip().startswith("TribalWars.updateGameData("):
            game_data = json.loads(line[line.index("(")+1:line.rindex(")")])
            return (game_data["player"]["id"], game_data["player"]["name"])
    return None

def write_keks(keks, id, name):
    directory = os.path.join(common.get_root_folder(), "keks", keks["domain"])
    filename = id+"_"+name
    file = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    with open(file, "w") as fd:
        fd.write(keks["sid"])

def import_from_text(text):
    keks = parse_keks(text)
    if keks is None:
        raise ValueError("Invalid keks: {0}".format(text))
    (id, name) = player_id_from_keks(keks)
    if id is None:
        raise ValueError("Session is expired or invalid")
    write_keks(keks, id, name)

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
        keks_file = os.path.join(common.get_root_folder(), "keks", domain, player_id+"_"+player)
        try:
            with open(keks_file) as fd:
                sid = fd.read()
        except:
            issues.append(dict(domain=domain, player=player, issue="notfound"))
            continue
        response = requests.get("https://" +  domain + "/game.php",
            cookies=dict(sid=sid), headers={"user-agent": common.USER_AGENT})
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
