#!/usr/bin/env python3
from dstimer import server, send_action

if __name__ == "__main__":
    send_action.DaemonThread().start()
    server.app.run()
