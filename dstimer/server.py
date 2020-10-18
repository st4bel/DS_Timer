from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
import dateutil.parser
from datetime import datetime
from dstimer import import_action
from dstimer import import_template
from dstimer import import_keks
from dstimer import __version__, __needUpdate__
from dstimer import delete_action
from dstimer import world_data
from dstimer import common
import dstimer.common as common
import dstimer.incomings_handler as incomings_handler
from dstimer.import_keks import check_and_save_sids
from operator import itemgetter, attrgetter
import logging
from dstimer.models import *
from dstimer import app, db
logger = logging.getLogger("dstimer")


def innocdn_url(path):
    #    return "https://dsde.innogamescdn.com/8.58/30847" + path
    return "https://dsde.innogamescdn.com/asset/3cc5e90" + path


def sids_status():
    try:
        with open(os.path.join(common.get_root_folder(), "status.txt")) as fd:
            return json.load(fd)
    except:
        return []


def get_templates():
    path = os.path.join(os.path.expanduser("~"), ".dstimer", "templates")
    templates = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            with open(os.path.join(path, filename)) as fd:
                units = json.load(fd)
            template = {}
            template["name"] = filename[:filename.rfind("_")]
            template["id"] = filename[filename.rfind("_") + 1:-9]
            template["units"] = units
            templates.append(template)
    return templates


def get_scheduled_actions(folder="schedule"):
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", folder)
    actions = []
    player = []
    village_data = None
    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
                if village_data is None:
                    village_data = world_data.get_village_data(action["domain"]) # bug wenn angriffe von mehreren welten geplant
                for dataset in village_data:
                    if action["source_id"] == int(dataset[0]):
                        action["source_village_name"] = world_data.unquote_name(dataset[1])
                    if action["target_id"] == int(dataset[0]):
                        action["target_village_name"] = world_data.unquote_name(dataset[1])
                action["departure_time"] = dateutil.parser.parse(action["departure_time"])
                action["arrival_time"] = dateutil.parser.parse(action["arrival_time"])
                action["world"] = action["domain"].partition(".")[0]
                action["id"] = file[file.rfind("_") + 1:-4]
                action["size"] = import_action.get_attack_size(action["units"])
                if action["player"] not in player:
                    player.append(action["player"])
                actions.append(action)
    return player, actions

def get_scheduled_actions_db(): #platzhalter funktion um abfrage db zu testen
    attacks = Attacks.query.all()
    actions = []
    player = []
    if len(attacks) == 0: 
        return player, actions
    village_data = world_data.get_village_data(attacks[0].player.domain) #platzhalter siehe oben
    for attack in attacks:
        action = attack.load_action()
        for dataset in village_data:
            if action["source_id"] == int(dataset[0]):
                action["source_village_name"] = world_data.unquote_name(dataset[1])
            if action["target_id"] == int(dataset[0]):
                action["target_village_name"] = world_data.unquote_name(dataset[1])
        action["world"] = action["domain"].partition(".")[0]
        action["size"] = import_action.get_attack_size(action["units"])
        if action["player"] not in player:
            player.append(action["player"])
        actions.append(action)
    return player, actions

def get_unitnames():
    return common.unitnames
    #return ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"]


def get_buildingnames():
    return common.buildingnames


def get_LZ_reduction():
    options = common.read_options()
    if options["LZ_reduction"] != {}:
        return import_action.check_LZ(options["LZ_reduction"])
    else:
        return {}


app.jinja_env.globals.update(innocdn_url=innocdn_url, version=__version__, sids_status=sids_status,
                             update=__needUpdate__, options=common.read_options(),
                             get_LZ_reduction=get_LZ_reduction)


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


#def sort_unit_dict(dict):
#    units = {"spear":0, "sword":1, "axe":2, "archer":3, "spy":4, "light":5, "marcher":6, "heavy":7, "ram":8, "catapult":9, "knight":10, "snob":11}


@app.route("/")
def index():
    return render_template("erklaerbaer.html")


@app.route("/schedule")
def schedule():
    player, actions = get_scheduled_actions()
    args = ""
    rev = ""
    if "sort" in request.args:
        args = request.args.get("sort")
        rev = request.args.get("reverse")
        if "true" in rev:
            rev_bool = True
            rev = "false"
        else:
            rev_bool = False
            rev = "true"
        if "coord" not in args:
            actions.sort(key=lambda x: x[args], reverse=rev_bool)
        else:    #target_coords or source_coord
            actions.sort(key=lambda x: x[args]["x"], reverse=rev_bool)
    return render_template("schedule.html", actions=actions, player=player, rev=rev)

@app.route("/schedule_db", methods=["GET"])
def schedule_db():
    player, actions = get_scheduled_actions_db()
    return render_template("schedule_db.html", actions = actions, player=player, rev="false")

@app.route("/schedule", methods=["POST"])
def schedule_post():
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    trash_path = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    type = request.form["type"]
    if "delete__all" == type:
        delete_action.delete_all()
        return redirect("/schedule")
    elif "delete_" in type:
        if delete_action.delete_single(id=type[7:len(type)]):
            return redirect("/schedule")    #reload
        return "ok"
    elif "edit_" in type:
        return redirect("/edit_action/" + type.split("_")[1])


@app.route("/import")
def import_action_get():
    return render_template("import_action.html")


@app.route("/import", methods=["POST"])
def import_action_post():
    try:
        text = request.form["text"]
        if request.form["type"] == "action":
            import_action.import_from_text(text=text, rand_mill=request.form.get("rand_mill"))
        elif request.form["type"] == "keks":
            import_keks.import_from_text(text)
            check_and_save_sids()
            world_data.refresh_world_data()
        return redirect("/schedule", code=302)
    except Exception as e:
        flash("{}: {}".format(type(e).__name__, e))
        return redirect(url_for("import_action_get", text=text))


@app.route("/wb")
def wb_get():
    return render_template("workbench_import.html")


@app.route("/wb", methods=["POST"])
def wb_post():
    try:
        text = request.form["text"]
        keks_path = os.path.join(common.get_root_folder(), "keks")
        players = []
        for folder in os.listdir(keks_path):
            for file in os.listdir(os.path.join(keks_path, folder)):
                s_file = file.split("_", 1)
                playername = common.filename_unescape(s_file[1])
        if playername == None:
            playername = request.form["playername"]
        if request.form["type"] == "wb_template":
            import_template.import_from_workbench(text)
            return redirect("/templates")
        elif request.form["type"] == "wb_action":
            import_action.import_wb_action(text, playername)
        return redirect("/schedule", code=302)
    except Exception as e:
        flash(str(e))
        #return redirect(url_for("wb_get", text=text))
        return redirect(url_for("wb_get"))


@app.route("/logs")
def logs():
    path = os.path.join(os.path.expanduser("~"), ".dstimer", "logs", "dstimer.log")
    with open(path) as file:
        logs = map(json.loads, reversed(file.read().splitlines()))
    return render_template("logs.html", logs=logs)


@app.route("/templates", methods=["GET"])
def templates_get():
    t = Template.query.all()
    if not Template.query.filter_by(is_default= True).first():
        flash("Keine Standard Template gesetzt!")
    return render_template("templates.html", templates=t, unitnames=get_unitnames())


@app.route("/templates", methods=["POST"])
def templates_post():
    units = get_unitnames()
    templates = Template.query.all()
    type = request.form["type"]
    if type == "create_template":
        template_units = {}
        for name in units:
            template_units[name] = request.form[name]
        t = Template()
        t.set_units(template_units)
        template_name = request.form["newname"]
        for template in templates:
            if template_name == template.name:
                flash("Template name already used.")
                return redirect(url_for("templates_get"))
        t.name = template_name
        db.session.add(t)
    elif "delete_" in type:
        id = int(type[7:len(type)])
        if id in [t.id for t in templates]:
            t = Template.query.filter_by(id=id).first()
            db.session.delete(t)
        #options = common.read_options()
        #for template in templates:
        #    if template["id"] == id:
        #        if options["evac_template"] == template["name"]:
        #            options["evac_template"] = "default"
        #            common.write_options(options)
        #            flash("Rausstell-Template auf default zurückgesetzt.")
        #import_template.remove_by_id(id)
    elif "set-default_" in type:
        id = int(type.split("_")[1])
        if id in [t.id for t in templates]:
            dt = Template.query.filter_by(is_default=True).first()
            if dt:
                dt.is_default = False
                db.session.add(dt)
            t = Template.query.filter_by(id=id).first()
            t.is_default = True
            db.session.add(t)
    db.session.commit()
    return redirect("/templates")
    #return redirect("/templates")


@app.route("/show/<domain>/<type>/<id>", methods=["GET"])    #TODO domain
def show(domain, type, id):
    player, actions = get_scheduled_actions()
    filtered_actions = []
    for action in actions:
        if str(action[type]) == id and action["domain"] == domain:
            action["milliseconds"] = int(action["arrival_time"].microsecond / 1000)
            filtered_actions.append(action)
    return jsonify(filtered_actions)


@app.route("/new_attack", methods=["GET"])
def new_atts_get():
    keks_path = os.path.join(common.get_root_folder(), "keks")
    players = []
    for folder in os.listdir(keks_path):
        for file in os.listdir(os.path.join(keks_path, folder)):
            s_file = file.split("_", 1)
            players.append({
                "domain": folder,
                "id": s_file[0],
                "name": common.filename_unescape(s_file[1])
            })
    return render_template("new_attack.html", templates=get_templates(), unitnames=get_unitnames(),
                           players=players, N_O_P=len(players), buildings=get_buildingnames())


@app.route("/new_attack", methods=["POST"])
def new_atts_post():
    action = {}
    action["source_coord"] = {"x": request.form["source_x"], "y": request.form["source_y"]}
    action["target_coord"] = {"x": request.form["target_x"], "y": request.form["target_y"]}
    unitnames = get_unitnames()
    action["units"] = {}
    for name in unitnames:
        if request.form[name] != "":
            action["units"][name] = request.form[name]
    if request.form.get("departure"):
        action["departure_time"] = request.form["time"]
    else:
        action["arrival_time"] = request.form["time"]
    source_player = request.form.get("source_player_select").split("+")
    action["player_id"] = source_player[0]
    action["domain"] = source_player[1]
    action["source_id"] = int(
        request.form.get("source_village")
        if request.form.get("source_village") != "" else world_data.get_village_id_from_coords(
            action["domain"], action["source_coord"]["x"], action["source_coord"]["y"]))
    action["target_id"] = int(
        request.form.get("target_village")
        if request.form.get("target_village") != "" else world_data.get_village_id_from_coords(
            action["domain"], action["target_coord"]["x"], action["target_coord"]["y"]))
    action["type"] = request.form["type"]
    action["player"] = world_data.get_player_name(action["domain"], action["player_id"])
    action["sitter"] = "0"
    action["vacation"] = "0"
    action["force"] = False

    if request.form.get("save_default_attack_building"):
        action["save_default_attack_building"] = 1
    else:
        action["save_default_attack_building"] = 0
    action["building"] = request.form.get("catapult_target")

    id = import_action.import_from_ui(action)
    return redirect("/schedule") if action["type"] != "multiple_attacks" else redirect(
        "/add_attacks/" + id)


@app.route("/add_attacks/<id>")
def add_attacks(id):
    player, actions = get_scheduled_actions("temp_action")
    for a in actions:
        if id == a["id"]:
            action = a
            action["target_player"] = world_data.get_player_name(
                action["domain"], world_data.get_village_owner(action["domain"],
                                                               action["target_id"]))
            break
    return render_template("add_attacks.html", templates=get_templates(), unitnames=get_unitnames(),
                           action=action)


@app.route("/add_attacks/<id>", methods=["POST"])
def add_attacks_post(id):
    NoA = int(request.form["type"])
    player, actions = get_scheduled_actions("temp_action")
    action = []
    for a in actions:
        if id == a["id"]:
            a["departure_time"] = str(a["departure_time"]).replace(" ", "T")
            del a["arrival_time"]
            action.append(a)
            break
    min_time_diff = common.read_options()["min_time_diff"]
    speed = import_action.speed(action[0]["units"], "",
                                import_action.get_cached_unit_info(action[0]["domain"]))
    action[0]["type"] = "attack"
    for i in range(1, NoA + 1):
        a = action[0].copy()
        a["units"] = {}
        for name in get_unitnames():
            n = name + "_" + str(i)
            if request.form[n] != "":
                a["units"][name] = request.form[n]
        if speed != import_action.speed(a["units"], "",
                                        import_action.get_cached_unit_info(a["domain"])):
            logger.info("change in unitspeed after adding attack")
            return redirect("/add_attacks/" + id)
        departure = a["departure_time"].split(".")
        if len(departure) == 1:
            departure.append(0)
        a["departure_time"] = departure[0] + "." + str(
            int(departure[1]) + (1000 * i * min_time_diff))
        action.append(a)
    for i in range(1, NoA + 1):
        action[NoA - i]["next_attack"] = import_action.import_from_ui(action[NoA + 1 - i])
    import_action.import_from_ui(action[0])
    delete_action.delete_single(id, "temp_action")
    return redirect("/schedule")


@app.route("/new_attack_show/<json_escaped>")
def create_action_show(json_escaped):
    return


@app.route("/edit_action/<id>", methods=["GET"])
def edit_action_get(id):
    player, actions = get_scheduled_actions()
    action = {}
    for a in actions:
        if id == a["id"]:
            action = a
            action["target_player"] = world_data.get_player_name(
                action["domain"], world_data.get_village_owner(action["domain"],
                                                               action["target_id"]))
            break
    keks_path = os.path.join(common.get_root_folder(), "keks")
    players = []
    for folder in os.listdir(keks_path):
        for file in os.listdir(os.path.join(keks_path, folder)):
            s_file = file.split("_", 1)
            players.append({
                "domain": folder,
                "id": s_file[0],
                "name": common.filename_unescape(s_file[1])
            })
    return render_template("edit_action.html", players=players, action=action,
                           unitnames=get_unitnames(), templates=get_templates(),
                           buildings=get_buildingnames())


@app.route("/edit_action/<id>", methods=["POST"])
def edit_action_post(id):
    if request.form["type"] == "abbort":
        return redirect("/schedule")
    action = {}
    action["source_coord"] = {"x": request.form["source_x"], "y": request.form["source_y"]}
    action["target_coord"] = {"x": request.form["target_x"], "y": request.form["target_y"]}
    unitnames = get_unitnames()
    action["units"] = {}
    for name in unitnames:
        if request.form[name] != "":
            action["units"][name] = request.form[name]
    if request.form.get("departure"):
        action["departure_time"] = request.form["time"]
    else:
        action["arrival_time"] = request.form["time"]
    source_player = request.form.get("source_player_select").split("+")
    action["player_id"] = source_player[0]
    action["domain"] = source_player[1]
    action["source_id"] = int(
        request.form.get("source_village")
        if request.form.get("source_village") != "" else world_data.get_village_id_from_coords(
            action["domain"], action["source_coord"]["x"], action["source_coord"]["y"]))
    action["target_id"] = int(
        request.form.get("target_village")
        if request.form.get("target_village") != "" else world_data.get_village_id_from_coords(
            action["domain"], action["target_coord"]["x"], action["target_coord"]["y"]))
    action["type"] = request.form["type"]
    action["player"] = world_data.get_player_name(action["domain"], action["player_id"])
    action["sitter"] = "0"
    action["vacation"] = "0"
    action["force"] = False

    if request.form.get("save_default_attack_building"):
        action["save_default_attack_building"] = 1
    else:
        action["save_default_attack_building"] = 0
    action["building"] = request.form.get("catapult_target")

    import_action.import_from_ui(action, id=id)
    return redirect("/schedule")


@app.route("/villages_of_player/<domain>/<player_id>")
def villages_of_player(domain, player_id):
    res = world_data.get_villages_of_player(domain, player_id=player_id)
    return jsonify(res)


@app.route("/load_players/<domain>")
def load_players(domain):
    res = world_data.get_players(domain)
    return jsonify(res)


@app.route("/delete_action/<id>")
def delete_single_action(id):
    if delete_action.delete_single(id):
        return "1"


@app.route("/options", methods=["GET"])
def options_get():
    return render_template("options.html", templates=get_templates())


@app.route("/options", methods=["POST"])
def options_post():
    options = common.read_options()
    if request.form["type"] == "refresh-world-data":
        world_data.refresh_world_data()
    elif request.form["type"] == "kata-target":
        logger.info("standard Kataziel ausgewählt: " + request.form.get("kata-target-menu"))
        options["kata-target"] = request.form.get("kata-target-menu")
    elif request.form["type"] == "reset-folders":
        common.reset_folders()
    elif request.form["type"] == "donate_toogle":
        options["show_donate"] = not options["show_donate"]
    elif request.form["type"] == "LZ_reduction":
        new_LZ = {
            "until": request.form.get("LZ_reduction_until"),
            "player": request.form.get("LZ_reduction_target_input"),
            "magnitude": request.form.get("LZ_reduction_percent_input"),
            "domain": request.form.get("LZ_reduction_domain_input")
        }
        options["LZ_reduction"] = import_action.check_LZ(new_LZ)
    elif request.form["type"] == "LZ_reduction_delete":
        options["LZ_reduction"] = {}
    elif request.form["type"] == "min_time_diff":
        options["min_time_diff"] = int(request.form.get("min_time_diff"))
    elif request.form["type"] == "evac_template":
        options["evac_template"] = request.form.get("evac_template")
    common.write_options(options)
    app.jinja_env.globals.update(options=options)
    return redirect("/options")

@app.route("/keks_overview", methods = ["GET"])
def keks_overview():
    players = Player.query.all()
    return render_template("keks_overview.html", players = players)        


@app.route("/incomings/<domain>/<player_id>", methods=["GET"])
def incomings_get(domain, player_id):
    player = Player.query.filter_by(domain=domain, player_id=player_id).first_or_404()
    incs_dict = incomings_handler.load_incomings(domain, player_id)
    incomings_handler.save_current_incs(incs_dict, domain, player_id)
    incs = Incomings.query.filter_by(player = player).all()
    return render_template("incomings.html", incs = incs)

@app.route("/inc_options/<domain>/<player_id>", methods=["GET"])
def inc_options(domain, player_id):
    p = Player.query.filter_by(player_id=player_id, domain = domain).first_or_404()
    p.refresh_groups()
    i = Inctype.query.all()
    t = Template.query.all()
    return render_template("inc_options.html", templates = t, player = p, inctypes = i)

@app.route("/inc_options/<domain>/<player_id>", methods=["POST"])
def inc_options_post(domain, player_id):
    p = Player.query.filter_by(player_id=player_id, domain = domain).first_or_404()
    i = Inctype.query.all()

    if request.form["type"] == "add_group":
        g = p.groups.filter_by(group_id=request.form.get("add_group_menu")).first()
        priority = int(request.form.get("add_group_priority"))
        if priority not in p.get_used_group_priorities():
            g.is_used = True
            g.priority = priority
            db.session.add(g)
        else:
            flash("Priorität <strong>{}</strong> bereits besetzt von Gruppe <strong>[{}]</strong>.".format(priority, p.groups.filter_by(is_used=True, priority=priority).first().name))
    
    elif request.form["type"] == "submit_changes":
        # mark groups as unused
        delete_groups = [int(group_id) for group_id in request.form.getlist("delete_group")]
        for group_id in delete_groups:
            g = p.groups.filter_by(group_id=group_id).first()
            g.is_used = False
            g.priority = None
            db.session.add(g)
        formnames = [name for name in request.form if "use-template_" in name]
        ignore = [name.split("_") for name in request.form.getlist("ignore")]
        for name in formnames:
            t_id = request.form.get(name)
            [group_id, inc_id] = name.split("_")[1:]
            e = Evacoption(
                group = Group.query.filter_by(group_id = group_id).first(), 
                inctype = Inctype.query.filter_by(id = inc_id).first(),
                template = Template.query.filter_by(id = t_id).first(),
                is_ignored = [group_id, inc_id] in ignore 
            )
            db.session.add(e)
                
    elif request.form["type"] == "refresh_groups":
        p.refresh_groups(1)

    db.session.commit()
    return redirect(url_for("inc_options", domain=domain, player_id=player_id))
    