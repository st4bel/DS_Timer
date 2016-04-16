import requests
from bs4 import BeautifulSoup
import re

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"

def get_place_screen(keks, village_id):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": USER_AGENT}
    params = dict(village=village_id, screen="place")
    response = requests.get("https://" + keks["domain"] + "/game.php", params=params, cookies=cookies, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.select("form#command-data-form")[0]
    units = dict()
    for input in form.select("input[id^=unit_input_]"):
        units[input["name"]] = int(input.find_next_sibling("a").get_text()[1:-1])
    data = dict()
    for input in form.select("input"):
        data[input["name"]] = input["value"]

    return (units, data)

def get_confirm_screen(keks, form, units, target_x, target_y, attack_or_support):
    cookies = dict(sid=keks["sid"])
    headers = {"user-agent": USER_AGENT}
    params = {"village": form["source_village"], "screen": "place", "try": "confirm"}

    payload = form.copy()
    if attack_or_support:
        del payload["support"]
    else:
        del payload["attack"]
    payload["x"] = target_x
    payload["y"] = target_y
    for unit in units:
        payload[unit] = units[unit]

    response = requests.post("https://" + keks["domain"] + "/game.php", params=params, cookies=cookies, headers=headers, data=payload)
    with open('out.html', 'w') as file:
        file.write(str(response.content, "utf-8"))

    soup = BeautifulSoup(response.content, 'html.parser')
    error_box = soup.select("div[class=error_box]")
    if len(error_box) >= 1:
        error = error_box[0].get_text().strip()
        print(error)
        return None

    form = soup.select("form#command-data-form")[0]
    action = form["action"]
    data = dict()
    for input in form.select("input"):
        if "name" in input.attrs and "value" in input.attrs:
            data[input["name"]] = input["value"]
    return (action, data)
