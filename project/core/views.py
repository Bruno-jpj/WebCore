from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse, # client GET request
    HttpResponseRedirect,
    StreamingHttpResponse,
    HttpResponseBadRequest,
    JsonResponse
)

# to decorate a def() just apply it
# if want to use it on CBV need to integrate: method_decorator
from .decorators import  check_log_in

from .forms import Loginform

from .models import (
    Macchinari,
    Informazioni,
    Allarmi,
    Componenti,
    Users,
)

from api.serializers import InformazioniSerializers

from enum import Enum
import json

# Create your views here.

# HTML Template
class TEMPLATE(Enum):
    INDEX = 'index.html'
    LOGIN = 'log_in.html'
    SIGNUP = 'sign_up.html'
    ALARM_PAGE = 'alarm_page.html'    
#

# WebApp views

# dispatch: center point of CBV(every request[GET/POST/etc.] pass through dispatch)
@method_decorator(check_log_in, name='dispatch')
class IndexLogic(View):
    def get(self, request: HttpRequest):
        # can return even an HTML file
        return render(request, TEMPLATE.INDEX.value)
    #
    def post(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
#
def login(request: HttpRequest):
    if request.method == "POST":
        form = Loginform(request.POST)

        # username get from the form
        in_username = request.POST.get("username")
        in_password = request.POST.get("password")

        try:
            user_obj = Users.objects.get(username = in_username)
            
            if check_password(in_password, user_obj.pwd):

                # put into session.user_id the id of the logged in user
                request.session['user_id'] = user_obj.id
                print("HERE")
                return redirect('index')
            else:
                messages.error(request, "Username o Password errati")
        except Users.DoesNotExist:
            messages.error(request, "Username o Password inesistenti")
    else:
        form = Loginform()

    request.session.cycle_key()
    #
    context = {
        'form': form
    }
    return render(request, TEMPLATE.LOGIN.value, context)
#
def logout(request: HttpRequest):
    try:
        request.session.flush()
        messages.info(request, "Succeded in logging out...")
        return redirect('index') # index = IndexLogic
    except Exception as e:
        return HttpResponse(f"ERROR: catch an error during log-out [{e}]")
#

def alarm_page(request: HttpRequest):
    if request.method == "POST":
        alarm_title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        solution_img = request.FILES.get("solution_img")
        solution_video = request.FILES.get("solution_video")
        #
    elif request.method == "GET":
        print("Search Pressed...")
    
    return render(request, TEMPLATE.ALARM_PAGE.value)


# API views
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