import requests
from bs4 import BeautifulSoup
from dstimer.models import Player, Group, Village
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
    player = Player.query.filter_by(player_id=player_id, domain=domain).first()
    with requests.Session() as session:
        session.cookies.set("sid", player.sid)
        session.headers.update({"user-agent": common.USER_AGENT})
        params = dict(screen = "overview_villages")
        headers = dict(referer = "https://" + domain + "/game.php")
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)
        check_reponse(response)

        soup = BeautifulSoup(response.content, "html.parser")

        group_links = soup.select(".group-menu-item")
        groups = dict()

        for link in group_links:
            groups[int(link["data-group-id"])] = strip_group_name(link.text)
    return groups

def refresh_groups(domain, player_id):
    player = Player.query.filter_by(player_id=player_id, domain=domain).first_or_404()
    if not player.is_active():
        return ["Session nicht aktiv, konnte Gruppen nicht aktualisieren."]
    loaded_groups = load_groups(domain, player_id)
    warnings = []
    for group in Group.query.filter_by(player = player):
        if group.group_id in loaded_groups: # Gruppe bereits gespeichert, ggf. name aktualisieren
            if group.name != loaded_groups[group.group_id]:
                warnings.append("Gruppenname geändert von [{}] zu [{}].".format(group.name, loaded_groups[group.group_id]))
                group.name = loaded_groups[group.group_id] 
                db.session.add(group)
            del loaded_groups[group.group_id] # aus loaded groups entfernen, damit nicht erneut darüber iteriert
        else: #Gruppe nicht mehr vorhanden.
            if group.is_used:
                warnings.append("Gruppe [{}] wurde vom Raussteller benutzt, ist mittlerweile aber nicht mehr vorhanden. Bitte Einstellungen überprüfen!".format(group.name))
            db.session.delete(group)
    
    for group_id in loaded_groups: # sind nur noch "neue" Gruppen
        g = Group(
            name = loaded_groups[group_id],
            group_id = group_id,
            player = player
        )
        db.session.add(g)
    db.session.commit()
    return warnings
    
def load_villages_of_group(domain, player_id, group_id):
    player = Player.query.filter_by(player_id=player_id, domain=domain).first()
    with requests.Session() as session:
        session.cookies.set("sid", player.sid)
        session.headers.update({"user-agent": common.USER_AGENT})
        params = dict(screen = "overview_villages", group = group_id)
        headers = dict(referer = "https://" + domain + "/game.php")
        response = session.get("https://" + domain + "/game.php", params=params, headers = headers)
        check_reponse(response)

        soup = BeautifulSoup(response.content, "html.parser")

        # get current overview mode: combined, prod, trader, ... 
        overview_menu = soup.select("table#overview_menu")[0]
        current_mode = overview_menu.select(".selected")[0].findChildren("a")[0]["href"].split("mode=")[1].split("&")[0]

        allowed_modes = [
            "combined",
            "prod",
            "units",
            "buildings",
            "tech",
            "groups"
        ]
        
        if current_mode not in allowed_modes:
            # neu laden in combined mode
            params["mode"] = "combined"
            response = session.get("https://" + domain + "/game.php", params=params, headers = headers)
            soup = BeautifulSoup(response.content, "html.parser")
            # reset overview_menu if necessary.
            params["mode"] = current_mode
            session.get("https://" + domain + "/game.php", params=params, headers = headers)
      
        
        # read villages in group
        village_name_span = soup.select("span.quickedit-vn")
        villages = []
        for village in village_name_span:
            villages.append(int(village["data-id"]))
        
        return villages

def refresh_villages_of_player(domain, player_id):
    # refreshes all relationships between villages and active groups of player.
    player = Player.query.filter_by(player_id=player_id, domain=domain).first()
    groups = Group.query.filter_by(player = player, is_used = True)
    #villages = Village.query.filter_by(player = player)

    for group in groups:
        loaded_villages = load_villages_of_group(domain, player_id, group.group_id)

        for village in group.villages:
            if village.village_id in loaded_villages:
                loaded_villages.remove(village.village_id)
            else:
                #remove relationship 
                group.remove_village(village)
        
        for village_id in loaded_villages:
            if village_id not in player.get_village_ids():
                village = Village(
                    player = player, 
                    village_id = village_id
                )
            else:
                village = Village.query.filter_by(village_id=village_id).first()
            group.add_village(village)
        db.session.add(group)
    db.session.commit()