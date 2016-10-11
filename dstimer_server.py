from flask import Flask, render_template, request, redirect
import os
import json
import dateutil.parser
from import_action import import_from_text
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World"

@app.route("/schedule")
def schedule():
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    actions = []
    for file in os.listdir(schedule_path):
        if os.path.isfile(os.path.join(schedule_path, file)):
            with open(os.path.join(schedule_path, file)) as fd:
                action = json.load(fd)
                action["departure_time"] = dateutil.parser.parse(action["departure_time"])
                action["arrival_time"] = dateutil.parser.parse(action["arrival_time"])
                action["world"] = action["domain"].partition(".")[0]
                actions.append(action)
    return render_template("schedule.html", actions=actions)

@app.route("/import")
def import_action_get():
    return render_template("import_action.html", text=request.args.get('text'))

@app.route("/import", methods=["POST"])
def import_action_post():
    text = request.form["text"]
    import_from_text(text)
    return redirect("/schedule", code=302)

if __name__ == "__main__":
    app.run()
