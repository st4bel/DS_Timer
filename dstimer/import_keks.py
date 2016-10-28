import requests
import json
import os
import re
from dstimer import common

FORMAT = re.compile(r"\[([a-zA-Z\.\-0-9]+)\|([a-zA-Z0-9%:]+)\|([a-zA-Z0-9]{8})\]")

def parse_keks(str):
    """Parse an exported session cookie string from DS Kekse."""
    match = FORMAT.search(str)
    if match:
        return dict(domain=match.group(1), sid=match.group(2))
    else:
        return None

def player_from_keks(keks):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": common.USER_AGENT}
    response = requests.get("https://" +  keks["domain"] + "/game.php",
        cookies=cookies, headers=headers)
    for line in response.content.decode("utf-8").splitlines():
        if line.strip().startswith("TribalWars.updateGameData("):
            game_data = json.loads(line[line.index("(")+1:line.rindex(")")])
            return game_data["player"]["name"]
    return None

def write_keks(keks, player):
    directory = os.path.join(common.get_root_folder(), "keks", keks["domain"])
    file = os.path.join(directory, player)
    os.makedirs(directory, exist_ok=True)
    with open(file, "w") as fd:
        fd.write(keks["sid"])

def import_from_text(text):
    keks = parse_keks(text)
    if keks is None:
        raise ValueError("Invalid keks: {0}".format(text))
    player = player_from_keks(keks)
    if player is None:
        raise ValueError("Session is expired or invalid")
    write_keks(keks, player)

def check_sids():
    schedule_path = os.path.join(common.get_root_folder(), "schedule")
    players_to_check = set()
    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
            players_to_check.add((action["domain"], action["player"]))

    issues = []
    for (domain, player) in players_to_check:
        keks_file = os.path.join(common.get_root_folder(), "keks", domain, player)
        try:
            with open(keks_file) as fd:
                sid = fd.read()
        except:
            issues.append(dict(domain=domain, player=player, issue="notfound"))
            continue
        if player_from_keks(dict(sid=sid, domain=domain)) is None:
            issues.append(dict(domain=domain, player=player, issue="invalid"))
    return issues

def check_and_save_sids():
    issues = check_sids()
    with open(os.path.join(common.get_root_folder(), "status.txt"), "w") as fd:
        json.dump(issues, fd)
