import requests

# endpoint Django
url = "http://127.0.0.1:8000/machine/search"

# dati da inviare
data = {
    "machine_code": "pp23240",
    "machine_type": "600",
    "machine_alarm": "temperature"
}

# invio POST con JSON
response = requests.post(url, json=data)

# stampa risposta
print("Status code:", response.status_code)

try:
    decoded_data = response.json()
    for key, value in decoded_data.items():
        print(f"{key}: {value}")
except:
    print("Response:", response.text)
finally:
    print("data sent...")