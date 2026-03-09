
## Esempio di View per ricezione dati JSON
@csrf_exempt => Used only if you don't have CSRF_token (ex. external API), needed if it not comes from a Django forms <br>

@csrf_exempt<br> 
def test_receive_data(request: HttpRequest):

    if request.method == "POST":
        try: 
            # 1. leggi il corpo della richiesta e converte la stringa JSON in dict
            data: dict = json.loads(request.body)

            # 2. data è un dictionary
            machine_code = data.get('machine_code')
            machine_type = data.get('machine_type')
            machine_alarm = data.get('machine_alarm')

            print("POST HERE")
            print(data)
            print(request.body)
                        
            return JsonResponse(data)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Json non valido...") 
               
    elif request.method == "GET": # dalla pagina 127.0.0.1:8000/macchine/search/ di opera arriva request tipo GET

        print(f"{machine_code}, \n {machine_type}, \n {machine_alarm}")

        print("GET HERE")
        data = {
            "machine_code": machine_code,
            "machine_type": machine_type,
            "machine_alarm": machine_alarm
        }

        # nella JSON Response è normale il dato ritorna null e si vede solo la key - per ottenere anche il dato deve essere preso dal DB 
        return JsonResponse(data)
    else:
        return HttpResponseBadRequest("Metodo non supportato")

## Endpoint Dinamico

### Parametri nella URL

#config/urls.py <br>
from django.urls import path <br>
from api import views <br>
urlpatterns = [
    path("api/search/<str:source>/", views.search),
]

#views.py
def search(request, source):

    if source == "ignition":
        # logica ignition
        pass

    elif source == "webapp":
        # logica webapp
        pass

### Example endpoint <br>
- /api/search/ignition/ <br>
- /api/search/webapp/

## Endpoint unico con logica interna

path("api/search/", views.search)

Distinzione basata su:
- campo JSON
- token
- header
- payload

Esempion JSON: <br>
{ <br>
  "source": "ignition", <br>
  "machine_id": "M01", <br>
  "alarm_code": "E102" <br>
}

# TEST-API con rest_framework
from rest_framework import ( <br>
    generics,<br>
    request,<br>
    response,<br>
    status,<br>
)

from rest_framework.views import APIView

from .serializers import (<br>
    MacchinariSerializers,<br>
    AllarmiSerializers,<br>
    ComponentiSerializers,<br>
    InformazioniSerializers<br>
)

from core.models import (<br>
    Macchinari,<br>
    Informazioni,<br>
    Allarmi,<br>
    Componenti<br>
)

from enum import Enum
import json


class MacchinariCreate(generics.ListCreateAPIView):

    # takes every machine that exists
    queryset = Macchinari.objects.all()

    # define serializer
    serializer_class = MacchinariSerializers

    def delete(self, request: request, *args, **kwargs):
        Macchinari.objects.all().delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
#
class InformazioniGet(generics.RetrieveAPIView):

    queryset = Informazioni.objects.all()

    serializer_class = InformazioniSerializers

    lookup_field = "pk"
#
class MacchinariUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Macchinari.objects.all()

    serializer_class = MacchinariSerializers

    lookup_field = "pk"
#

## TEST_API URLs

    # api/urls.py
    path('create-macchine/', views.MacchinariCreate.as_view(), name="create-macchine"),
    path('get-info/<int:pk>/', views.InformazioniGet.as_view(), name="get-info"),
    path('update-delete-macchine/<int:pk>/', views.MacchinariUpdateDelete.as_view(), name="update-delete-macchinari"),
    # path('search/', views.test_receive_data, name='receive_data'),

#
    # raggruppo gli endpoint dell'API
    path('macchine/', include('api.urls')),


### Steps

- ritoccare il DB