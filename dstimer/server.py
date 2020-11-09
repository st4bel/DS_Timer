from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import os, ast
import json
import dateutil.parser
from datetime import datetime, timedelta
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

def get_scheduled_data_db(attacks):
    # returns data by which a filter could be apllied
    sources = dict()
    targets = dict()
    #target_players = dict()
    stati  = ["active", "finished","expired", "failed"]
    
    if attacks:
        village_data = dict()
        for attack in attacks:
            if str(attack.source_id) not in sources:
                sources[str(attack.source_id)] = attack.source_name
            if str(attack.target_id) not in targets:
                targets[str(attack.target_id)] = attack.target_name
            if attack.player.domain not in village_data:
                village_data[attack.player.domain] = world_data.get_village_data(attack.player.domain)
            #target_player_id = None
            #for dataset in village_data[attack.player.domain]:
            #    if attack.target_id == int(dataset[0]):
            #        target_player_id = int(dataset[4])
            #if target_player_id:
            #    if target_player_id not in target_players:
            #        target_players[target_player_id] = world_data.get_player_name(attack.player.domain, target_player_id)
            #if attack.status not in stati:
            #    stati.append(attack.status)
    return sources, targets, stati

def get_incomings_data(incs):
    # returns data by which a filter could be apllied
    sources = dict()
    targets = dict()
    source_players = dict()
    names = []
    units = []
    templates = dict()

    if incs:
        for inc in incs:
            if str(inc.source_village_id) not in sources:
                sources[str(inc.source_village_id)] = inc.source_village_name
            if str(inc.target_village_id) not in targets:
                targets[str(inc.target_village_id)] = inc.target_village_name
            if str(inc.source_player_id) not in source_players:
                source_players[str(inc.source_player_id)] = inc.source_player_name
            if inc.slowest_unit not in units:
                units.append(inc.slowest_unit)
            if inc.name not in names:
                names.append(inc.name)
            if inc.template:
                if str(inc.template.id) not in templates:
                    templates[str(inc.template.id)] = inc.template.name
            elif "None" not in templates:
                templates["None"] = "Ignoriert"
    data = dict(
        sources=sources,
        targets=targets,
        source_players=source_players,
        units=units, 
        names=names,
        templates=templates)
    return data


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
    attacks = Attacks.query.order_by("departure_time").all()
    templates = Template.query.all()
    sources, targets, stati = get_scheduled_data_db(attacks)
    filter_by = ast.literal_eval(request.args.get('filter_by') if request.args.get('filter_by') else "{}")
    order_by = request.args.get('order_by')
    if filter_by:
        query_filter_by = dict()
        # cant filter by unit, status, evac directly. 
        if "source_id" in filter_by:
            query_filter_by["source_id"] = filter_by["source_id"]
        if "target_id" in filter_by:
            query_filter_by["target_id"] = filter_by["target_id"]

        attacks = Attacks.query.filter_by(**query_filter_by).order_by("departure_time").all()

        if "unit" in filter_by:
            attacks = [attack for attack in attacks if filter_by["unit"] in attack.get_units()]
        if "evac" in filter_by:
            if filter_by["evac"] == "1":
                attacks = [attack for attack in attacks if attack.incs.all()]

    if "status" not in filter_by:
        attacks = [attack for attack in attacks if not attack.is_expired()]
    else:
        if filter_by["status"] == "active":
            attacks = [attack for attack in attacks if not attack.is_expired()]
        elif filter_by["status"] == "expired":
            attacks = [attack for attack in attacks if attack.status == "expired"]
        elif filter_by["status"] == "finished":
            attacks = [attack for attack in attacks if attack.status == "finished"]
        else:
            attacks = [attack for attack in attacks if attack.status == "failed"]
    
    if order_by: # jaja noch sehr lui haft
        if "arrival_time" == order_by:
            attacks = sorted(attacks, key=lambda a: a.arrival_time)

    return render_template("schedule_db.html", attacks = attacks, units = common.unitnames, sources = sources, targets = targets, stati = stati, filter_by = filter_by, buildings = common.buildingnames, templates = templates)

@app.route("/schedule_db", methods=["POST"])
def schedule_db_post():
    type = request.form["type"]
    current_filter_by = ast.literal_eval(request.args.get('filter_by') if request.args.get('filter_by') else "{}")
    filter_by = dict()
    if "apply_filter" in type:
        for filter in [name for name in request.form if "filter_" in name]:
            if request.form.get(filter) != "default":
                filter_by[filter.split("filter_by_")[1]] = request.form.get(filter)
        return redirect(url_for("schedule_db", filter_by=filter_by))
    elif "delete__all" in type:
        attacks = Attacks.query.filter_by(**current_filter_by).all()
        for attack in attacks:
            db.session.delete(attack)
    elif "delete__selected" in type:
        for a_id in request.form.getlist("selected"):
            attack = Attacks.query.filter_by(id = int(a_id)).first()
            db.session.delete(attack)
    elif "delete_" in type:
        attack = Attacks.query.filter_by(id = int(type.split("_")[1])).first()
        db.session.delete(attack)
    elif "edit_" in type:
        id = type.split("_")[1]
        attack = Attacks.query.filter_by(id = int(id)).first()
        
        if request.form.get("edit_template_"+id) != "default":
            attack.template = Template.query.filter_by(id = int(request.form.get("edit_template_"+id))).first()

        units = dict()
        for unit in common.unitnames:
            units[unit] = request.form.get("edit_unit_"+unit+"_"+id) if request.form.get("edit_unit_"+unit+"_"+id) != "" else 0
        
        if attack.template:
            if attack.template.get_units() != units:
                #template currently set, but now units changed manually -> delete relationship to template
                attack.template = None

        attack.units = str(units)

        if request.form.get("edit_template_"+id) != "default":
            attack.template = Template.query.filter_by(id = int(request.form.get("edit_template_"+id))).first()

        departure = dateutil.parser.parse(request.form.get("edit_departure_"+id))
        arrival = dateutil.parser.parse(request.form.get("edit_arrival_"+id))

        if departure != attack.departure_time or arrival != attack.arrival_time:
            duration = import_action.runtime(
                import_action.speed(attack.get_units(), attack.type, import_action.get_cached_unit_info(attack.player.domain)),
                import_action.distance(dict(x=attack.source_coord_x, y=attack.source_coord_y), dict(x=attack.target_coord_x, y=attack.target_coord_y)), attack.player.domain)

            if departure != attack.departure_time:
                attack.departure_time = departure
                attack.arrival_time = attack.departure_time + duration
            else:
                attack.arrival_time = arrival
                attack.departure_time = attack.arrival_time - duration
        
        attack.building = request.form.get("edit_building_"+id)

        if attack.status != "scheduled" and not attack.is_expired():
            attack.status = "scheduled"
        
        attack.autocomplete()
        db.session.add(attack)
    elif "apply_complex" in type:
        diff = timedelta(
            hours = int(request.form.get("move_by_hours")),
            minutes = int(request.form.get("move_by_minutes")),
            seconds = int(request.form.get("move_by_seconds")),
            microseconds = int(request.form.get("move_by_ms"))*1000
        )
        template = request.form.get("set_template_all")
        building = request.form.get("set_building_all")
    
        for a_id in request.form.getlist("selected"):
            attack = Attacks.query.filter_by(id = int(a_id)).first()
            attack.departure_time = attack.departure_time + diff
            attack.arrival_time = attack.arrival_time + diff
            if template != "default":
                attack.template = Template.query.filter_by(id = int(template)).first()
            if building != "default":
                attack.building = building
            db.session.add(attack)
            
    db.session.commit()

    return redirect(url_for("schedule_db", filter_by = current_filter_by))

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
        return redirect("/dashboard", code=302)
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
    name = request.args.get('name') if request.args.get('name') else ""
    units = ast.literal_eval(request.args.get('units') if request.args.get('units') else "{}")
    if not Template.query.filter_by(is_default= True).first():
        flash("Keine Standard Template gesetzt!")
    return render_template("templates.html", templates=t, unitnames=get_unitnames(), current_name = name, current_units = units)


@app.route("/templates", methods=["POST"])
def templates_post():
    units = get_unitnames()
    templates = Template.query.all()
    type = request.form["type"]
    if type == "new_template":
        template_units = {}
        for name in units:
            template_units[name] = request.form.get("new_template_unit_"+name)
        t = Template()
        t.set_units(template_units)
        template_name = request.form.get("new_template_name")
        for template in templates:
            if template_name == template.name:
                flash("Template name already used.")
                return redirect(url_for("templates_get", name=template_name, units = template_units))
        t.name = template_name
        db.session.add(t)
    elif "delete_" in type:
        id = int(type[7:len(type)])
        if id in [t.id for t in templates]:
            t = Template.query.filter_by(id=id).first()
            db.session.delete(t)
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
    elif "edit_template_" in type:
        id = type.split("_")[2]
        t = Template.query.filter_by(id=int(id)).first()
        template_units = dict()
        for name in units:
            template_units[name] = request.form.get("new_template_unit_"+name)
        t.set_units(template_units)
        template_name = request.form.get("new_template_name")
        if template_name != t.name:
            for template in templates:
                if template_name == template.name:
                    flash("Template name already used.")
                    return redirect(url_for("templates_get", name=template_name, units = template_units))
        t.name = template_name
        db.session.add(t)

    db.session.commit()
    return redirect("/templates")

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
    incs = Incomings.query.filter_by(player = player).order_by("arrival_time").all()
    templates = Template.query.all()
    filter_by = ast.literal_eval(request.args.get('filter_by') if request.args.get('filter_by') else "{}")
    data = get_incomings_data(incs)
    if filter_by:
        if "source_id" in filter_by:
            incs = [inc for inc in incs if inc.source_village_id == int(filter_by["source_id"])]
        if "target_id" in filter_by:
            incs = [inc for inc in incs if inc.target_village_id == int(filter_by["target_id"])]
        if "source_player_id" in filter_by:
            incs = [inc for inc in incs if inc.source_player_id == int(filter_by["source_player_id"])]
        if "slowest_unit" in filter_by:
            incs = [inc for inc in incs if inc.slowest_unit == filter_by["slowest_unit"]]
        if "template" in filter_by:
            if filter_by["template"] != "None":
                incs = [inc for inc in incs if inc.template if inc.template.id == filter_by["template"]]
            else:
                incs = [inc for inc in incs if not inc.template]
        if "name" in filter_by:
            incs = [inc for inc in incs if filter_by["name"] in inc.name]
    return render_template("incomings.html", incs = incs, filter_by = filter_by, data = data, templates = templates)

@app.route("/incomings/<domain>/<player_id>", methods=["POST"])
def incomings_post(domain, player_id):
    type = request.form["type"]

    current_filter_by = ast.literal_eval(request.args.get('filter_by') if request.args.get('filter_by') else "{}")
    filter_by = dict()
    if "apply_filter" in type:
        for filter in [name for name in request.form if "filter_" in name]:
            if request.form.get(filter) != "default" and request.form.get(filter) != "":
                filter_by[filter.split("filter_by_")[1]] = request.form.get(filter)
        return redirect(url_for("incomings_get", domain = domain, player_id = player_id, filter_by=filter_by))
    return redirect(url_for("incomings_get", domain = domain, player_id = player_id, filter_by = current_filter_by))

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
            group = Group.query.filter_by(group_id = group_id).first()
            inctype = Inctype.query.filter_by(id = inc_id).first()

            e = Evacoption.query.filter_by(group = group, inctype = inctype).first()
            if not e:
                e = Evacoption(
                    group = group, 
                    inctype = inctype, 
                )
            e.template = Template.query.filter_by(id = t_id).first()
            e.is_ignored = [group_id, inc_id] in ignore

            db.session.add(e)
                
    elif request.form["type"] == "refresh_groups":
        p.refresh_groups(1)

    elif request.form["type"] == "activate":
        p.evac_activated = not p.evac_activated

    db.session.commit()
    return redirect(url_for("inc_options", domain=domain, player_id=player_id))

@app.route("/dashboard", methods=["GET"])
def dashboard_get():
    players = Player.query.all()
    atts = dict()
    incs = dict()
    for player in players:
        attacks = Attacks.query.filter_by(player=player).all()
        incomings = Incomings.query.filter_by(player=player).all()
        # counting amount of scheduled+pending, finished, exprired, failed atts
        NO_active = len([attack for attack in attacks if not attack.is_expired()]) 
        NO_finished = len([attack for attack in attacks if attack.status == "finished"])
        NO_expired = len([attack for attack in attacks if attack.status == "expired"])
        NO_failed = len([attack for attack in attacks if attack.status == "failed"])
        NO_incs = len(incomings)
        NO_ignored_incs = len([incoming for incoming in incomings if not incoming.template])

        atts[player.id] = dict(
            active = {"NO" : NO_active, "badge" : "", "filter_by" : str(dict(status = "active"))},
            finished = {"NO" : NO_finished, "badge" : "alert-success", "filter_by" : str(dict(status = "finished"))},
            expired = {"NO" : NO_expired, "badge" : "alert-warning", "filter_by" : str(dict(status = "expired"))},
            failed = {"NO" : NO_failed, "badge" : "alert-danger", "filter_by" : str(dict(status = "failed"))}
        )
        incs[player.id] = dict(
            incs = NO_incs,
            ignored = NO_ignored_incs
        )
    if not Template.query.filter_by(is_default= True).first():
        flash("Keine Standard Template gesetzt!")

    return render_template("dashboard.html", players=players, atts=atts, incs = incs)
