import os
import requests
from dstimer import common

def get_server_files(domain):
    directory = os.path.join(common.get_root_folder(), "world_data", domain)
    os.makedirs(directory, exist_ok=True)
    look_at = ["village", "player"]
    for name in look_at:
        url = "https://"+domain+"/map/"+name+".txt"
        file = requests.get(url)
        filename = os.path.join(directory, name+".txt")
        open(filename, "wb").write(file.content)
