from django.views.decorators.csrf import (
    csrf_exempt, 
    csrf_protect, 
    requires_csrf_token
) 

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    MacchinariSerializers,
    AllarmiSerializers,
    ComponentiSerializers,
    InformazioniSerializers
)

from core.models import (
    Informazioni,
    Macchinari,
    Componenti,
    AllarmiSoluzioni
)


from enum import Enum
import json

# Create your views here.

'''
ex. received JSON: {
    "machine_code": "pp23240",
    "machine_type": "600",
    "machine_alarm": "temperatura"
}
'''
class RequestEvent(APIView):
    # uso una def post perchè nel mentre che il client invia i dati al server; 
    # il server li rimanda indietro nello stesso endpoint
    def post(self, request: Request):
        try:
            received_data = request.data
            print(f"API Received Data: [{received_data}]")

            '''
            Devo fare il migrate delle tabelle di log

            api_log = ApiRequestLog.objects.create(
                endpoint = "info/",
                payload = received_data,
                response_status = 200
            )

            api_log.save()
            '''

            result = handle_api_call(received_data)

            return Response(result) # send away JSON serialized data
        except Exception as e:
            print(f"Server Error: {e}")
            return Response({"error": str(e)}, status=500)
    #
#
def handle_api_call(api_data: dict):
    machine_code = api_data.get("machine_code")
    machine_type = api_data.get("machine_type")
    machine_alarm = api_data.get("machine_alarm")

    # logic 
    print(f"Data Received: \n {machine_code} \n {machine_type} \n {machine_alarm}")

    # get data from DB
    try:
        machines_obj = Macchinari.objects.get(piano_produzione = machine_code)
        alarms_obj = AllarmiSoluzioni.objects.get(titolo = machine_alarm)
    except Macchinari.DoesNotExist:
        return {"ERROR": f"Piano Produzione Macchina [{machine_code}] non trovato..."}
    except AllarmiSoluzioni.DoesNotExist:
        return {"ERROR":f"Allarme [{machine_alarm}] non trovato..."}
    
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
#