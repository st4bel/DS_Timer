import requests
from bs4 import BeautifulSoup
from dstimer.models import Player, Group
from dstimer import db, common

def check_reponse(response):
    if response.url.endswith("/sid_wrong.php"):
        raise ValueError("Session is invalid")

def strip_group_name(text):
    if "[" in text:
        return text.split("[")[1].split("]")[0]
    else:
        return text.split(">")[1].split("<")[0]

def load_groups(domain, player_id):
    player = Player.query.filter_by(player_id=player_id, domain=domain).first_or_404()
    with requests.Session() as session:
        session.cookies.set("sid", player.sid)
        session.headers.update({"user-agent": common.USER_AGENT})
        params = dict(screen = "overview_villages")
        headers = dict(referer = "https://" + domain + "/game.php")
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)
        check_reponse(response)

        soup = BeautifulSoup(response.content, "html.parser")

        group_links = soup.select("a.group-menu-item")
        groups = dict()

        for link in group_links:
            groups[int(link["data-group-id"])] = strip_group_name(link.text)
    return groups

def refresh_groups(domain, player_id):
    player = Player.query.filter_by(player_id=player_id, domain=domain).first_or_404()
    loaded_groups = load_groups(domain, player_id)

    for group in Group.query.filter_by(player = player):
        if group.group_id in loaded_groups: # Gruppe bereits gespeichert, ggf. name aktualisieren
            if group.name != loaded_groups[group.group_id]:
                group.name = loaded_groups[group.group_id] 
                db.session.add(group)
            del loaded_groups[group.group_id] # aus loaded groups entfernen, damit nicht erneut darüber iteriert
        else: #Gruppe nicht mehr vorhanden.
            db.session.delete(group)
    
    for group_id in loaded_groups: # sind nur noch "neue" Gruppen
        g = Group(
            name = loaded_groups[group_id],
            group_id = group_id,
            player = player
        )
        db.session.add(g)
    db.session.commit()
    