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

# here there is all the logic 

'''
ex. received JSON: {
    "machine_code": "pp23240",
    "machine_type": "600",
    "machine_alarm": "temperatura"
}
'''
class RequestEvent(APIView):
    # I use a def POST because the client send data to the server
    # the server work with them, return a response and send it back
    def post(self, request: Request):
        try:
            # see if the API received any data by printing it
            received_data = request.data
            print(f"API Received Data: [{received_data}]")

            '''
            api_log = ApiRequestLog.objects.create(
                endpoint = URL_Request,
                payload = received_data,
                response_status = 200
                header = Client_API_Key
            )

            api_log.save()
            '''
            # pass the data to the logic and retrieve it
            result = handle_api_call(received_data)

            # send away JSON serialized data
            return Response(result) 
        except Exception as e:
            # in case of exception I throw an error and HTTP status code 500[Server Error]
            print(f"Server Error: {e}")
            return Response({"error": str(e)}, status=500)
    #
#
def handle_api_call(api_data: dict):
    # receive data from the API, trying to unpack it [ key: value ]
    machine_code = api_data.get("machine_code")
    machine_type = api_data.get("machine_type")
    machine_alarm = api_data.get("machine_alarm")

    # print what I received
    print(f"Data Received: \n {machine_code} \n {machine_type} \n {machine_alarm}")

    # filter / get data from the DB, like a SQL query and creating 2 obj with the result
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

    # another filter like select with joins on foreign key
    info_queryset = Informazioni.objects.filter(
        id_macchinario = machines_obj.id, 
        id_allarme = alarms_obj.id
    )

    # print the result of the query
    print(f"info_queryset: \n [{info_queryset}]")
    
    # init a serializer to transform data in a JSON likeformat
    serializer = InformazioniSerializers(info_queryset, many=True)
    
    # send the result to the API
    return {"status": "ok", "data": serializer.data}    
#