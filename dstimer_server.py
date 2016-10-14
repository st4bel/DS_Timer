#!/usr/bin/env python3
from dstimer import server, send_action
import logging
from logging import handlers
import os
from pythonjsonlogger import jsonlogger

if __name__ == "__main__":
    # init logger
    log_dir = os.path.join(os.path.expanduser("~"), ".dstimer", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "dstimer.log")
    logger = logging.getLogger("dstimer")
    logger.setLevel(logging.DEBUG)
    handler = handlers.TimedRotatingFileHandler(log_path, when="D")
    formatter = jsonlogger.JsonFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    send_action.DaemonThread().start()
    server.app.run()
