import requests
import json

import time


# endpoint Django
url = "http://127.0.0.1:8000/request/info/"

# dati da inviare
post_data = {
    "machine_code": "pp23240",
    "machine_type": "600",
    "machine_alarm": "temperatura"
}

try:
    # invio POST di dati JSON nell'URL
    print("POST Request...")
    request_post = requests.post(url, json=post_data)
except TimeoutError:
    print("TimeOutError...")


# stampa risposta
print("Request Status code:", request_post.status_code)

time.sleep(3)

print(f" GET Request Data: {request_post.json()}")
