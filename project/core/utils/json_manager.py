import json

class JsonManager:

    def __init__(self, json_path, conf_path):
        self.json_path = json_path
        self.conf_path = conf_path

    def read_alarm_json(self):
        with open(self.json_path, "r") as f:
            return json.load(f)

    def write_alarm_json(self, data):
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=4)

    def read_conf(self):
        with open(self.conf_path, "r") as f:
            return json.load(f)

    def write_conf(self, data):
        with open(self.conf_path, "w") as f:
            json.dump(data, f, indent=4)