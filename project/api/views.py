from django.views.decorators.csrf import (
    csrf_exempt, 
    csrf_protect, 
    requires_csrf_token
) 

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from core.views import handle_api_call

from .serializers import (
    MacchinariSerializers,
    AllarmiSerializers,
    ComponentiSerializers,
    InformazioniSerializers
)

from .models import ApiRequestLog

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