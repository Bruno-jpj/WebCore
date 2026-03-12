import json

JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\script\json\allarmi_soluzioni.json'

with open(JSON_PATH, 'r') as file:
    alarm_list: dict = json.load(file)

# converts a Python object (such as a dictionary or list) into a JSON-formatted string. 
# It is mainly used when you need to send data over APIs, store structured data or serialize Python objects into JSON text.
# print(json.dumps(alarm_list, indent=4))

# accedere a dict annidato

alarm_name = "Allarme_Sensore"

print(json.dumps(alarm_list["lista_allarmi"], indent=4))

# accesso diretto al dict
# print(alarm_list["lista_allarmi"][alarm_name]["media"]["video"])

# nome_allarme = set(alarm_list["lista_allarmi"])

# print(alarm_list["lista_allarmi"][alarm_name]["media"]["img"]["path_file"])