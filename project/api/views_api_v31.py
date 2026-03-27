from django.views.decorators.csrf import (
    csrf_exempt, 
    csrf_protect, 
    requires_csrf_token
) 

from rest_framework.pagination import CursorPagination, LimitOffsetPagination, PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, exceptions, generics

from .serializers import(
    MacchinariSerializers,
    AllarmiSerializers,
    InformazioniSerializers
)

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

'''
URL: request/info/v2

ex. received JSON: {
    "data":[{
        "api_key": "client_key", # header
        "language": "text_it", # text_it = default
        "machine_code": "pp23240", # codice identificativo della macchina
        "machine_category":"TR",
        "machine_type": "600",
        "machine_alarm": "temperatura" # codice identificativo dell'allarme   
    }]
}
'''

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
def create_api_log(request: HttpRequest, client_key, language, machine_code, machine_category, machine_type, machine_alarm, response_status, api_key):
    
    payload: dict = {
        "client_key": client_key,
        "language": language,
        "machine_code": machine_code,
        "machine_category": machine_category,
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
class MachineAlarmCursorPagination(CursorPagination):
    page_size = 1000 # records per page
    page_size_query_param = 'page_size' # Optional: Allow the client to set the pagesize with " ?page_size=1100 "
    max_page_size = 1500
    # cursor fields, same order like in the SQL index, inside () must be present a UNIQUE / PK element
    # Django think of FK 'id_macchinario' as an obj, so use id_macchinario_id to indicate the int value
    # Must be in the query .values() or just don't use .values() and serialize before sending
    ordering = ('id_macchinario_id','id')
    cursor_query_param = 'cursor' # URL parameter (default)
    #
    # Puoi usare questo metodo per custom response
    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        prev_link = self.get_previous_link()
        #
        return Response({
            'next': next_link,
            'previous': prev_link,
            'has_next': next_link is not None, # return True or False
            'has_previous': prev_link is not None, # return True or False
            'results': data
        }, status=status.HTTP_200_OK)
#
'''
class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data,
            'status': status.HTTP_200_OK
        })
#'''
class RequestEvent(APIView):
    # init pagination class
    pagination_class = MachineAlarmCursorPagination
    #
    def get(self, request:Request):
        try:

            received_data = request.data
            
            if received_data is not None:
                
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
                    client_key = received_data.get("client_key")
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
                        language = received_data.get("language")
                    except language is None or not languages_dict.get(language):
                        api_logger_view(language, "variabile language è None, imposto la lingua in 'it' ")
                        language = languages_dict.get("text_it")
                    #
                    machine_code = received_data.get("machine_code") # ex: pp23240 / None
                    machine_category = received_data.get("machine_category") # ex: TR
                    machine_type = received_data.get("machine_type") # ex: 600
                    machine_alarm = received_data.get("machine_alarm") # ex: temperature / None
                    #
                    filters: dict = {}

                    if machine_code:
                        filters['id_macchinario__piano_produzione'] = machine_code

                    if machine_alarm:
                        filters['id_allarme__titolo'] = machine_alarm

                    queryset = Informazioni.objects.select_related(
                        'id_macchinario', 'id_allarme'
                    ).filter(**filters)
                    
                    # creates logs
                    api_logger_view(queryset.count(), "QuerySet:")
                    create_api_log(request, client_key, language, machine_code, machine_category, machine_type, machine_alarm, status.HTTP_200_OK, api_key)
                    
                    
                    api_logger_view(Informazioni.objects.filter(id_macchinario__isnull=True).count(), "Numero FK macchinari null")
                    api_logger_view(Informazioni.objects.filter(id_allarme__isnull=True).count(), "Numero FK allarmi null")

                    # init istance of paginator
                    paginator = self.pagination_class()
                    
                    # without .values() queryset is a list with insede all the objects => list(obj_1, obj_2, obj_n)
                    serializer = {
                        "allarme":queryset[0].id_allarme.titolo,
                        "soluzione": queryset[0].id_allarme.__setattr__(AllarmiSoluzioni.objects.name, language),
                        "img":queryset[0].id_allarme.img,
                        "video":queryset[0].id_allarme.video
                    }
                    
                    # apply pagination to the queryset
                    # page will contain the element * page_size (max: page_size)
                    page = paginator.paginate_queryset(serializer, request)
                    api_logger_view(page, "Number of elements per Query")
                    #
                    if queryset is None:
                        return paginator.get_paginated_response(page)
                        # return Response({"data": queryset}, status=status.HTTP_404_NOT_FOUND) # if queryset is None return only the ID ???
                    else:
                        
                        # status code 201 because with this I know the queryset is not empty and it was sent back in the response
                        create_api_log(request, client_key, language, machine_code, machine_category, machine_type, machine_alarm, status.HTTP_201_CREATED, api_key)
                        
                        # return Response({"data": queryset}, status=status.HTTP_200_OK)
                        
                        # give back the paginated response in JSON format
                        # get_paginated_response adds automaticaly 'results', 'next', 'previous', 'has_next', 'has_previous'
                        return paginator.get_paginated_response(page)
                    #
                else:
                    api_logger_view(None, "Client-Key è vuota, non procedo.")
                    create_api_log(request, client_key, language, machine_code, machine_category, machine_type, machine_alarm, status.HTTP_200_OK, api_key)
            #    
            else:
                return Response({"Error":"None data received"}, status=status.HTTP_400_BAD_REQUEST)    
        except Exception as e:
            api_logger_view(e, "catch except of GET-RequestEvent")
            return Response({"Error": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR,)
    #
    def post(self, request):
        return Response({"Error: Request can't be resolved"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    #
    def delete(self, request:Request):
        return Response({"Error: Request can't be resolved"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    #
    def put(self, request:Request):
        return Response({"Error: Request can't be resolved"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    #
    def patch(self, request:Request):
        return Response({"Error: Request can't be resolved"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    #
#  