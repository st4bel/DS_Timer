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
    token_input = form.select("input[type=hidden]")[0]

    return dict(units=units, token_name=token_input["name"], token_value=token_input["value"])
