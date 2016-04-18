import sys
import requests
import json
import os
from tkinter import Tk
import kekse

def player_from_keks(keks):
    cookies = dict(sid=keks["sid"])
    #TODO headers = {"user-agent": USER_AGENT}
    response = requests.get("https://" +  keks["domain"] + "/game.php",
        cookies=cookies) # headers=headers
    for line in response.content.decode("utf-8").splitlines():
        if line.strip().startswith("var game_data = {"):
            game_data = json.loads(line[line.index("=")+1:line.rindex(";")])
            return game_data["player"]["name"]
    return None

def write_keks(keks, player):
    directory = os.path.join(os.path.expanduser("~"), ".dstimer", "keks", keks["domain"])
    file = os.path.join(directory, player)
    os.makedirs(directory, exist_ok=True)
    with open(file, "w") as fd:
        fd.write(keks["sid"])

def main():
    if len(sys.argv) == 1:
        text = Tk().clipboard_get()
    else:
        text = sys.argv[1]
    keks = kekse.parse(text)
    if keks is None:
        print("Invalid keks: {0}".format(text))
        sys.exit(1)
    player = player_from_keks(keks)
    if player is None:
        print("Session is expired or invalid")
        sys.exit(1)
    write_keks(keks, player)

if __name__ == "__main__":
    main()
