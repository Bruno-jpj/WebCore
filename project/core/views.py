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
    AllarmiSoluzioni,
    Componenti,
    Users,
)

from api.serializers import InformazioniSerializers

from enum import Enum
from collections import namedtuple

import json
import configparser

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

class AlarmPage(View):
    class LANGUAGE(Enum):
        IT = 'it'
        EN = 'en'
        ESP = 'esp'
        FR = 'fr'
        DE = 'de'
        PT = 'pt' # portoghese
        FI = 'fi' # finlandese
        SE = 'se' # svedese
        NR = 'nr' # norvegese
        PL = 'pl' # polacco
        DK = 'dk' # danese
        RU = 'ru'
    #
    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\script\json\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'

    json_update = None
    db_update = None

    def get(self, request: HttpRequest):

        # read the json files
        cfg_dict: dict = self.read_conf_json(request)
        alarm_dict: dict = self.read_alarm_json(request)

        # take all elements from the tabel -> return a QuerySet
        alarm_solution = AllarmiSoluzioni.objects.all()

        
        # check if found at least one element in the table
        db_num_alarm = alarm_solution.count()

        # check found number of element in the JSON
        json_num_alarm = len(set(alarm_dict["lista_allarmi"]))

        if db_num_alarm >= json_num_alarm:
            print(f"INFO: Trovato: [{db_num_alarm}] elementi nel DB...")
            messages.info(request, f"INFO: Trovato {db_num_alarm} elementi nel DB")
        else:
            print(f"INFO: Trovato: [{db_num_alarm}] elementi nel DB...")
            messages.info(request, "INFO: Nessun elemento trovato... Inizio Upload da file di configurazione...")
            try:
                self.upload_from_json(alarm_dict)
            except Exception as e:
                print(f"Upload Func Error: [{e}]")
            finally:
                print("Finito...Controlla i risultati...")
        #
        context = {
            'alarms': alarm_solution
        }
        
        return render(request, TEMPLATE.ALARM_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        return HttpResponse("Btn non programmato ancora...")
    #
    def read_conf_json(self, request: HttpRequest) -> dict:
        with open(self.CONF_PATH, 'r') as file:
            cfg_dict: dict = json.load(file)

        return cfg_dict
    #
    def read_alarm_json(self, request: HttpRequest) -> dict:

        # read and transform to python dict
        with open(self.JSON_PATH, 'r') as file:
            alarm_dict: dict = json.load(file)

        return alarm_dict
    #
    def upload_from_json(self, alarm_dict: dict):
        
        # set with only the alarm titles
        alarm_set = set(alarm_dict["lista_allarmi"])

        for alarm_name in alarm_set:
            try: 
                temp_obj = AllarmiSoluzioni.objects.get(titolo = alarm_name)
                print(f"Già esiste: [{temp_obj}]")
            except AllarmiSoluzioni.DoesNotExist:
                try:
                    # create the object and auto-save it
                    AllarmiSoluzioni.objects.create(
                        titolo = alarm_name,
                        text_it = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                        text_eng = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                        text_esp = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                        text_de = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                        text_fr = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                        text_dk = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                        text_pt = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                        text_ru = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                        text_pl = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                        text_no = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                        text_se = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                        img = alarm_dict["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                        video = alarm_dict["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                        )
                    #
                except Exception as e:
                    print(f"Upload from Json Except: [{e}]")
            else:
                print(f"Gia esiste: [{temp_obj}]")
        #
        '''
        STESSA COSA SCRITTA SOPRA FORSE MEGLIO: 

        for alarm_name in alarm_set:
            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=alarm_name,
                defaults={
                    "text_it": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                    "text_eng": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                    "text_esp": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                    "text_de": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                    "text_fr": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                    "text_dk": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                    "text_pt": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                    "text_ru": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                    "text_pl": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                    "text_no": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                    "text_se": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                    "img": alarm_dict["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                    "video": alarm_dict["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                }
            )
            if created:
                print(f"Creato nuovo allarme: [{obj.titolo}]")
            else:
                print(f"Gia esiste: [{obj.titolo}]")
        '''          

