import requests
import json
import os
import re

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
    #TODO headers = {"user-agent": USER_AGENT}
    response = requests.get("https://" +  keks["domain"] + "/game.php",
        cookies=cookies) # headers=headers
    for line in response.content.decode("utf-8").splitlines():
        if line.strip().startswith("TribalWars.updateGameData("):
            game_data = json.loads(line[line.index("(")+1:line.rindex(")")])
            return game_data["player"]["name"]
    return None

def write_keks(keks, player):
    directory = os.path.join(os.path.expanduser("~"), ".dstimer", "keks", keks["domain"])
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
