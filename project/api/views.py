from django.views.decorators.csrf import (
    csrf_exempt, 
    csrf_protect, 
    requires_csrf_token
) 

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, exceptions

from core.models import (
    Informazioni,
    Macchinari,
    AllarmiSoluzioni
)
from .models import(
    ApiKeys,
    ApiRequestLogs,
    CoreRequestLogs
)

from django.http import HttpRequest


from datetime import datetime, timezone
from enum import Enum

import json

def api_logger_view(var, msg):
    path = '/var/www/webcore/project/api_debug.log'
    # directory = os.path.dirname(path)
    
    try:
        # check if the dir exists
        # os.makedirs(directory, exist_ok=True) 
        
        # 'a' = append and create in case if file not exists
        with open(path, 'a') as f:  
            f.write(f"[{msg} \n {var} \n {datetime.now(timezone.utc)}]\n ####################### \n")
    except Exception as e:
        #print(f"Logger Error: {e}")
        return Response(f"Eccezzione Log api logger: {e}")
#
'''
URL: request/info/

ex. received JSON: {    
    "api_key": "client_key", # header
    "language": "text_it", # text_it = default
    "machine_code": "pp23240", # codice identificativo della macchina
    "machine_category":"TR",
    "machine_type": "600",
    "machine_alarm": "temperatura" # codice identificativo dell'allarme
}
'''
#
class RequestEvent(APIView):
    def get(self, request: Request):
        return Response({"Error: Endpoint doesn't exists"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    #
    def post(self, request: Request):
        try:
            received_data = request.data
            
            if received_data is not None:
                
                api_logger_view(received_data, "Error: Catturata eccezzione nell'API POST")
                
                result = handle_post_call(received_data, request)  
                
                api_logger_view(result, "Result of POST-API call")
                
                return Response(result)
            else:
                return Response({"Error":"None data received"}, status=status.HTTP_400_BAD_REQUEST)    
        except Exception as e:
            
            api_logger_view(e, "Catch Except of POST-RequestEvent")
            
            return Response({"Error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
def create_api_log(request: HttpRequest, client_key, language, machine_code, machine_type, machine_alarm, response_status, api_key):
    
    payload: dict = {
        "client_key": client_key,
        "language": language,
        "machine_code": machine_code,
        "machine_type": machine_type,
        "machine_alarm": machine_alarm
    }
        
    ApiRequestLogs.objects.create(
        endpoint = request.path,
        payload = payload,
        response_status = response_status,
        api = api_key
    )  
#
def handle_post_call(api_data: dict, request: HttpRequest):
    
    languages_dict: dict = {
        "text_it": "text_it",
        "text_eng": "text_eng",
        "text_esp": "text_esp",
        "text_de": "text_de",
        "text_fr": "text_fr",
        "text_dk": "text_dk",
        "text_pt": "text_pt",
        "text_ru": "text_ru",
        "text_pl": "text_pl",
        "text_no": "text_no",
        "text_se": "text_se",
    }
    
    #
    try:
        client_key = api_data.get("client_key")
    except Exception as e:
        api_logger_view(e, f"Chiave del cliente non trovata: [{client_key}]")
    #
    if client_key is not None:
        #
        try:
            api_key = ApiKeys.objects.get(header = client_key)
        except ApiKeys.DoesNotExist:
            return {"Error": f"Chiave Client non esiste"}
        #
        try:
            language = api_data.get("language")
        except language is None or not languages_dict.get(language):
            api_logger_view(language, "variabile language è None, imposto la lingua in 'it' ")
            language = languages_dict.get("text_it")
        #
        machine_code = api_data.get("machine_code") # ex: pp23240 / None
        machine_category = api_data.get("machine_category") # ex: TR
        machine_type = api_data.get("machine_type") # ex: 600
        machine_alarm = api_data.get("machine_alarm") # ex: temperature / None
        #
        filters: dict = {}

        if machine_code:
            filters['id_macchinario__piano_produzione'] = machine_code

        if machine_alarm:
            filters['id_allarme__titolo'] = machine_alarm

        info_qs = Informazioni.objects.select_related(
            'id_macchinario', 'id_allarme'
        ).filter(
            **filters
        ).values(
            'id',
            'id_macchinario__piano_produzione',
            'id_allarme__titolo',
            f'id_allarme__{language}',
            'id_allarme__img',
            'id_allarme__video'
        )
        #
        api_logger_view(info_qs, "QuerySet:")
        #
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_200_OK, api_key)
        #
        if info_qs is None:
            return {"status": status.HTTP_204_NO_CONTENT, "data": info_qs} # if info_qs is None return only the ID ???
        else:
            
            # status code 201 because with this I know the info_qs is not empty and it was sent back in the response
            create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_201_CREATED, api_key)
            
            return {"status": status.HTTP_200_OK, "data": info_qs}
        #
    else:
        api_logger_view(None, "Client-Key è vuota, non procedo.")
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_200_OK, api_key)
#
    