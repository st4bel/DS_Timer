#!/usr/bin/env python3
from dstimer import server, send_action
import logging
from logging import handlers
import os, sys
from pythonjsonlogger import jsonlogger
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Attack Helper for Die Staemme")
    parser.add_argument("--host", help="Bind the server on this address", default="127.0.0.1")
    parser.add_argument("--port", help="Bind the server on this port", default=5000)
    parser.add_argument("--allow-root", help="Allow to start server with root or sudo", action="store_true")
    args = parser.parse_args()

    if "getuid" in dir(os) and os.getuid() == 0 and not args.allow_root:
        print("Starting DS_Timer as root or with sudo is disabled. Use --allow-root")
        sys.exit(1)

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
    server.app.run(host=args.host, port=args.port)
