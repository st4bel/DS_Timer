# DS-Timer package
import requests
from version_parser import Version

__version__ = "v0.6.6-dev"

__key__ = "insert key here lol"
__stdOptions__ = {
    "show_donate": True,
    "version": __version__,
    "LZ_reduction": {},
    "min_time_diff": 150,
    "kata-target": "default",
    "evac_template": "default"
}

try:
    request_release = requests.get("https://api.github.com/repos/st4bel/DS_Timer/releases/latest")
    json_release = request_release.json()
    __needUpdate__ = Version(__version__) < Version(json_release["name"])
except:    # if latest Version or current Version cant be parsed
    __needUpdate__ = False

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

import logging
from logging import handlers
import os, sys
from pythonjsonlogger import jsonlogger

app = Flask(__name__)
app.secret_key = 'ds_timer'
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(os.path.join(os.path.expanduser("~"), ".dstimer"), 'app.db')
db = SQLAlchemy(app)
#db.create_all()
import dstimer.models as models
models.init_db()

import argparse

parser = argparse.ArgumentParser(description="Attack Helper for Die Staemme")
parser.add_argument("--host", help="Bind the server on this address", default="127.0.0.1")
parser.add_argument("--port", help="Bind the server on this port", default=5000)
parser.add_argument("--allow-root", help="Allow to start server with root or sudo", action="store_true")
parser.add_argument("--open-browser", help="Open browser tab with dashboard after startup", action="store_true")
args = parser.parse_args()
from dstimer import server, models, send_action, common, world_data
common.create_folder_structure()

os.environ['TZ'] = 'Europe/Berlin'

    # init logger
log_dir = os.path.join(common.get_root_folder(), "logs")    #C:\Users\<username>\.dstimer\logs
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "dstimer.log")
logger = logging.getLogger("dstimer")
logger.setLevel(logging.DEBUG)
handler = handlers.TimedRotatingFileHandler(log_path, when="D")
formatter = jsonlogger.JsonFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

#world_data.refresh_world_data()

send_action.DaemonThread().start()


