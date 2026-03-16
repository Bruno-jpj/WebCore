import json

class JsonManager:

    # decentralize logic to manage read/write operation with JSON files
    def __init__(self, json_path, conf_path, json_back_path):
        self.json_path = json_path
        self.conf_path = conf_path
        self.json_backup_path = json_back_path

    # Alarm file
    def read_alarm_json(self):
        with open(self.json_path, "r") as f:
            return json.load(f)

    def write_alarm_json(self, data):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # Configuration file
    def read_conf(self):
        with open(self.conf_path, "r") as f:
            return json.load(f)

    def write_conf(self, data):
        with open(self.conf_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # Backup Alarm file
    def read_backup_json(self):
        with open(self.json_backup_path, "r") as f:
            return json.load(f)
    
    def write_backup_json(self, data):
        with open(self.json_backup_path, "w", encoding="utf-8") as f:
            return json.dump(data, f, indent=4)