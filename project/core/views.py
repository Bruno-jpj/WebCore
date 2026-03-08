from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.views import View
from django.contrib import messages

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse, # client GET request
    HttpResponseRedirect,
    StreamingHttpResponse,
    HttpResponseBadRequest,
    JsonResponse
)

from .models import (
    Macchinari,
    Informazioni,
    Allarmi,
    Componenti
)

from api.serializers import InformazioniSerializers

from enum import Enum
import json

# Create your views here.

def index(request: HttpRequest):

    # can return even an HTML file
    return HttpResponse("INDEX PAGE HERE....")
#
'''
ex. received JSON: {
    "machine_code": "pp23240", -> unique
    "machine_type": "600",
    "machine_alarm": "temperatura"
}
'''

def handle_api_call(api_data: dict):
    machine_code = api_data.get("machine_code")
    machine_type = api_data.get("machine_type")
    machine_alarm = api_data.get("machine_alarm")

    # logic 
    print(f"Data Received: \n {machine_code} \n {machine_type} \n {machine_alarm}")

    # get data from DB
    try:
        machines_obj = Macchinari.objects.get(piano_produzione = machine_code)
        alarms_obj = Allarmi.objects.get(titolo = machine_alarm)
    except Macchinari.DoesNotExist:
        return {"ERROR": f"Piano Produzione Macchina [{machine_code}] non trovato..."}
    except Allarmi.DoesNotExist:
        return {"ERROR":f"Allarme [{machine_alarm}] non trovato..."}

    print("HERE")

    '''
    # - get() restituisce un singolo oggetto o solleva un'eccezione
    # - filter() restituisce sempre una QuerySet (lista di oggetti), anche vuota.
    try:
        # query filter logic
        info_queryset = Informazioni.objects.get(
            id_macchinario = machines_obj.id, 
            id_allarme = alarms_obj.id
            )
    except Informazioni.DoesNotExist:
        return {"ERROR":f"Non trovato Informazioni riguardo MachineID: [{machines_obj.id}] AllarmeID: [{alarms_obj.id}]"}'''

    # query filter logic
    info_queryset = Informazioni.objects.filter(
        id_macchinario = machines_obj.id, 
        id_allarme = alarms_obj.id
    )

    print(f"info_queryset: \n [{info_queryset}]")

    serializer = InformazioniSerializers(info_queryset, many=True)
    
    return {"status": "ok", "data": serializer.data}