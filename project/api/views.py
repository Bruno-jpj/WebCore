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

from enum import Enum
import json

# here there is all the logic 

def logger_view(var, msg):
    path = '/var/www/webcore/project/debug.log'
    
    with open(path, 'a') as f:  # 'a' = append
        f.write(f"[{msg} \n {var} \n {datetime.datetime.now()}]\n ####################### \n")
#

'''
URL: request/info/

ex. received JSON: {
    "api_key": "client_key", # header
    "language": "text_it",
    "machine_code": "pp23240",
    "machine_type": "600",
    "machine_alarm": "temperatura"
}
'''
class RequestEvent(APIView):
    def get(self, request: Request):
        pass
    #
    def post(self, request: Request):
        
        try:
            received_data = request.data
            
            if received_data is not None:
                
                #print(f"API received Data [{received_data}]")
                logger_view(received_data, "ERRORE: Catturata eccezzione nella view: signup.")
                
                result = handle_post_call(received_data, request)
                
                logger_view(result, "Result of POST API call")
                
                return Response(result)
                
            else:
                return Response({"Error":"None data received"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            #print(f"API Server Error [{e}]")
            logger_view(e, "Catch Except of POST-RequestEvent")
            return Response({"Error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
def handle_post_call(api_data: dict, request: HttpRequest):
    
    languages: dict = {
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
    
    # process data from the API, trying to unpack [key: value]
    try:
        client_key = api_data.get("client_key") # de!fwD!ef@LFJ2434JII@
        language = api_data.get("language") # language for the texts
        machine_code = api_data.get("machine_code") # pp23240
        machine_type = api_data.get("machine_type") # 600
        machine_alarm = api_data.get("machine_alarm") # ALM_Temperaura_1000
        
    except Exception as e:
        logger_view(e, "Valori non trovati nella request")
        # print(f"valori non trovati nella request: [{e}]")
        
    # print(f"\nData Received: \n{client_key}\n{language}\n{machine_code}\n{machine_type}\n{machine_alarm}")

    api_key = 1
    
    # filter / get data from the DB, like a SQL query and creating 2 obj with the result
    try:
        machine_obj = Macchinari.objects.get(piano_produzione = machine_code)
        alarm_obj = AllarmiSoluzioni.objects.get(titolo = machine_alarm)
        api_key = ApiKeys.objects.get(header = client_key)
        
        # status code 302 because I know this obj were found and created
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_302_FOUND, api_key)
        
    except Macchinari.DoesNotExist:
        
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_404_NOT_FOUND, api_key)
        
        return {"ERROR": f"Piano Produzione Macchina [{machine_code}] non trovato..."}
    except AllarmiSoluzioni.DoesNotExist:
        
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_404_NOT_FOUND, api_key)
        
        return {"ERROR":f"Allarme [{machine_alarm}] non trovato..."}        
    except ApiKeys.DoesNotExist:
        
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_404_NOT_FOUND, api_key)
        
        return {"ERROR": f"Chiave cliente non trovata..."}
    except Exception as e:
        print(f"generico...{e}")
    
    if not (languages.get(language) and language):
        
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_404_NOT_FOUND, api_key)
        
        return {"ERROR": f"Lingua selezionata non trovata tra le disponibili"}
    

    # EX: Query con FK 
    # id_macchinario => Macchinari
    # id_allarme => AllarmiSoluzioni
    
    # 1) select_related: Fa le JOIN interne verso Macchinari e AllarmiSoluzioni in un’unica query
    # 2) filter: filtra sulle condizioni come il WHERE usando le FK ' __ ' per scendere nei campi collegati
    # 3) values: seleziona solo le colonne che vuoi
    info_qs = Informazioni.objects.select_related('id_macchinario', 'id_allarme').filter(
    id_allarme__titolo=alarm_obj.titolo,
    id_macchinario__piano_produzione=machine_obj.piano_produzione
    ).values(
        'id',  # corrisponde all'id della tab. Informazioni
        'id_macchinario__piano_produzione',
        'id_allarme__titolo',
        f'id_allarme__{language}',
        'id_allarme__img',
        'id_allarme__video'
    )
    
    print("infoqs")
    print(info_qs)
    
    # I don't use the serializers because I can't build the JSON reponse to pass it back so I did manually
    # info_qs is a list with inside a dictionary
    serializer = {
        "id": info_qs[0].get('id'),
        "allarme": info_qs[0].get('id_allarme__titolo'),
        "soluzione": info_qs[0].get(f'id_allarme__{language}'),
        "img": info_qs[0].get('id_allarme__img'),
        "video":info_qs[0].get('id_allarme__video')
    }
    
    if serializer is None:
        return {"status": status.HTTP_204_NO_CONTENT, "data": serializer} # return only the ID: 14
    else:
        
        # status code 201 because with this I know the serializer is not empty and it was sent back in the response
        create_api_log(request, client_key, language, machine_code, machine_type, machine_alarm, status.HTTP_201_CREATED, api_key)
        
        return {"status": status.HTTP_200_OK, "data": serializer}
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