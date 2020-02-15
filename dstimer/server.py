from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
import os
import json
import dateutil.parser
from dstimer import import_action
from dstimer import import_template
from dstimer import import_keks
from dstimer import __version__
from dstimer import delete_action
import dstimer.common as common
from dstimer.import_keks import check_and_save_sids
from operator import itemgetter, attrgetter
app = Flask(__name__)
app.secret_key = 'ds_timer'

def innocdn_url(path):
#    return "https://dsde.innogamescdn.com/8.58/30847" + path
    return "https://dsde.innogamescdn.com/asset/e9773236" + path

def sids_status():
    try:
        with open(os.path.join(common.get_root_folder(), "status.txt")) as fd:
            return json.load(fd)
    except:
        return []

app.jinja_env.globals.update(innocdn_url=innocdn_url, version=__version__, sids_status=sids_status)

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

    unitnames = ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"]
    return render_template("templates.html", templates=templates, unitnames=unitnames)

@app.route("/templates", methods=["POST"])
def templates_post():
    units = ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"]
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

@app.route("/show", methods=["get"])
def show_planned_atts():
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    source_id = request.args.get("source_id")
    target_id = request.args.get("target_id")
    actions = []
    for file in os.listdir(schedule_path):
        with open(os.path.join(schedule_path, file)) as fd:
            action = json.load(fd)
            if (source_id==str(action["source_id"]) or source_id==None) and (target_id==str(action["target_id"]) or target_id == None):
                action["id"] = file[file.rfind("_")+1:-4]
                actions.append(action)

    return render_template("show.html",actions=actions)
