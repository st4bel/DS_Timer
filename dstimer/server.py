from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
from flask.json import jsonify
import os
import json
import dateutil.parser
from dstimer import import_action
from dstimer import import_template
from dstimer import import_keks
from dstimer import __version__, __needUpdate__
from dstimer import delete_action
from dstimer import world_data
from dstimer import common
import dstimer.common as common
from dstimer.import_keks import check_and_save_sids
from operator import itemgetter, attrgetter
import logging
from flask_cors import CORS
app = Flask(__name__)
app.secret_key = 'ds_timer'
CORS(app)

logger = logging.getLogger("dstimer")

def innocdn_url(path):
#    return "https://dsde.innogamescdn.com/8.58/30847" + path
    return "https://dsde.innogamescdn.com/asset/e9773236" + path

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
            template={}
            template["name"]=filename[:filename.rfind("_")]
            template["id"]=filename[filename.rfind("_")+1:-9]
            template["units"]=units
            templates.append(template)
    return templates

def get_scheduled_actions():
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    actions = []
    player = []
    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
                action["departure_time"]    = dateutil.parser.parse(action["departure_time"])
                action["arrival_time"]      = dateutil.parser.parse(action["arrival_time"])
                action["world"]             = action["domain"].partition(".")[0]
                action["id"]                = file[file.rfind("_")+1:-4]
                if action["player"] not in player:
                    player.append(action["player"])
                actions.append(action)
    return player, actions

def get_unitnames():
    return ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"]

app.jinja_env.globals.update(innocdn_url=innocdn_url, version=__version__, sids_status=sids_status, update = __needUpdate__)

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
    args=""
    rev=""
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
            actions.sort(key=lambda x: x[args],reverse = rev_bool)
        else: #target_coords or source_coord
            actions.sort(key=lambda x: x[args]["x"],reverse = rev_bool)
    return render_template("schedule.html", actions=actions, player=player, rev=rev)

@app.route("/schedule", methods=["POST"])
def schedule_post():
    schedule_path   = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    trash_path      = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    type = request.form["type"]
    if "delete__all" in type:
        delete_action.delete_all()
        return redirect ("/schedule")
    elif "delete_" in type:
        if delete_action.delete_single(id=type[7:len(type)]):
            return redirect ("/schedule") #reload
        return "ok"

@app.route("/import")
def import_action_get():
    return render_template("import_action.html")

@app.route("/import", methods=["POST"])
def import_action_post():
    try:
        text = request.form["text"]
        if request.form["type"] == "action":
            import_action.import_from_text(text = text, rand_mill = request.form.get("rand_mill"))
        elif request.form["type"] == "keks":
            import_keks.import_from_text(text)
            check_and_save_sids()
        return redirect("/schedule", code=302)
    except Exception as e:
        flash("{}: {}".format(type(e).__name__,e))
        return redirect(url_for("import_action_get", text=text))

@app.route("/wb")
def wb_get():
    return render_template("workbench_import.html")

@app.route("/wb", methods=["POST"])
def wb_post():
    try:
        text = request.form["text"]
        playername = request.form["playername"]
        if request.form["type"] == "wb_template":
            import_template.import_from_workbench(text)
            return redirect("/templates")
        elif request.form["type"] == "wb_action":
            import_action.import_wb_action(text,playername)
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

@app.route("/templates")
def action_templates():
    return render_template("templates.html", templates = get_templates(), unitnames = get_unitnames())

@app.route("/templates", methods=["POST"])
def templates_post():
    units = get_unitnames()
    type = request.form["type"]
    if type == "create_template":
        template_units = {}
        for name in units:
            template_units[name] = request.form[name]
        template = {}
        template["name"] = request.form["newname"]
        template["units"] = template_units
        import_template.import_as_json(template)
        return redirect("/templates")
    elif "delete_" in type:
        id  = type[7:len(type)]
        import_template.remove_by_id(id)
        return redirect("/templates")
    #return redirect("/templates")


@app.route("/show/<domain>/<type>/<id>", methods=["GET"]) #TODO domain
def show(domain, type, id):
    player, actions = get_scheduled_actions()
    filtered_actions = []
    logger.info(type)
    logger.info(id)
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
            players.append({"domain" : folder, "id" : s_file[0], "name" : common.filename_unescape(s_file[1])})
    return render_template("new_attack.html", templates = get_templates(), unitnames = get_unitnames(), players=players, N_O_P = len(players))

@app.route("/new_attack", methods=["POST"])
def new_atts_post():
    action = {}
    action["source_coord"] = {"x" : request.form["source_x"], "y" : request.form["source_y"]}
    action["target_coord"] = {"x" : request.form["target_x"], "y" : request.form["target_y"]}
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
    action["source_id"] = int(request.form.get("source_village") if request.form.get("source_village") != "" else world_data.get_village_id_from_coords(action["domain"],action["source_coord"]["x"], action["source_coord"]["y"]))
    action["target_id"] = int(request.form.get("target_village") if request.form.get("target_village") != "" else world_data.get_village_id_from_coords(action["domain"],action["target_coord"]["x"], action["target_coord"]["y"]))
    action["type"] = request.form["type"]
    action["player"] = world_data.get_player_name(action["domain"], action["player_id"])
    action["sitter"] = "0"
    action["vacation"] = "0"
    action["force"] = False
    import_action.import_from_ui(action)
    return redirect("/schedule")

@app.route("/villages_of_player/<domain>/<player_id>")
def villages_of_player(domain, player_id):
    res = world_data.get_villages_of_player(domain, player_id=player_id)
    return jsonify(res)

@app.route("/load_players/<domain>")
def load_players(domain):
    res = world_data.get_players(domain)
    return jsonify(res)

@app.route("/options", methods=["GET"])
def options_get():
    return render_template("options.html")

@app.route("/options", methods=["POST"])
def options_post():
    if request.form["type"] == "refresh-world-data":
        world_data.refresh_world_data()
    elif request.form["type"] == "reset-folders":
        common.reset_folders()
    return redirect("/options")
