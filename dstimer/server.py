from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
import os
import json
import dateutil.parser
from dstimer import import_action
from dstimer import import_keks
from dstimer import __version__
import dstimer.common as common
from dstimer.import_keks import check_and_save_sids
app = Flask(__name__)
app.secret_key = 'ds_timer'

def innocdn_url(path):
    return "https://dsde.innogamescdn.com/8.58/30847" + path

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
                action["id"]                = file[file.find("_")+1:len(file)-4]
                if action["player"] not in player:
                    player.append(action["player"])
                actions.append(action)
    return render_template("schedule.html", actions=actions, player=player)

@app.route("/schedule", methods=["POST"])
def schedule_post():
    schedule_path   = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    trash_path      = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    type = request.form["type"]
    if "delete_" in type:
        id  = type[7:len(type)]
        for file in os.listdir(schedule_path):
            if id in file:
                os.rename(os.path.join(schedule_path, file), os.path.join(trash_path, file))
                return redirect ("/schedule") #reload

@app.route("/import")
def import_action_get():
    return render_template("import_action.html")

@app.route("/import", methods=["POST"])
def import_action_post():
    try:
        text = request.form["text"]
        if request.form["type"] == "action":
            import_action.import_from_text(text)
        elif request.form["type"] == "keks":
            import_keks.import_from_text(text)
            check_and_save_sids()
        return redirect("/schedule", code=302)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("import_action_get", text=text))

@app.route("/logs")
def logs():
    path = os.path.join(os.path.expanduser("~"), ".dstimer", "logs", "dstimer.log")
    with open(path) as file:
        logs = map(json.loads, reversed(file.read().splitlines()))
    return render_template("logs.html", logs=logs)
