from flask import Flask, render_template
import os
import json
import dateutil.parser
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
                action["world"] = action["domain"].partition(".")[0]
                actions.append(action)
    return render_template("schedule.html", actions=actions)

if __name__ == "__main__":
    app.run()
