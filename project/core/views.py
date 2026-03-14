from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin


from django.http import (
    Http404,
    HttpRequest,
    HttpResponse, # client GET request
    HttpResponseRedirect,
    StreamingHttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    FileResponse
)

# to decorate a def() just apply it
# if want to use it on CBV need to integrate: method_decorator
from .decorators import  check_log_in

from .forms import (
    SearchAlarmsForm, 
    ChoseLanguage
)

from .models import (
    Macchinari,
    Informazioni,
    AllarmiSoluzioni,
    Componenti,
    Users,
    LanguageModel
)

from reportlab.pdfgen import canvas, pdfimages
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Image

from .utils.json_manager import JsonManager

from enum import Enum
from collections import namedtuple
from googletrans import Translator

import json
import configparser
import time
import io
import csv

# Create your views here.

# HTML Template
class TEMPLATE(Enum):
    INDEX = 'index.html'
    LOGIN = 'log_in.html'
    SIGNUP = 'sign_up.html'
    MANUAL_PAGE = 'manual.html'
    CONTACTS = 'contacts.html'
    ACCOUNT = 'account.html'
    LINE = 'line.html'
#
# Index Page Logic
@check_log_in
class IndexLogic(View):
    def get(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def post(self, request: HttpRequest):
        #
        return render(request, TEMPLATE.INDEX.value)
    #
# Login
def login(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = Users.objects.get(username=username)
            if check_password(password, user.pwd):
                request.session['user_id'] = user.id
                return redirect('index')
            else:
                messages.error(request, "Username o Password errati")
        except Users.DoesNotExist:
            messages.error(request, "Username o Password inesistenti")
        return redirect('login')
    return render(request, TEMPLATE.LOGIN.value)
# Signup
def signup(request: HttpRequest):
    try:
        if request.method == "POST":
            in_username = request.POST.get("username")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            #
            if not all([in_username, password1, password2]):
                messages.error(request, "INFO: Tutti i campi devono essere compilati")
                return redirect('signup')
            #
            if password1 != password2:
                messages.error(request, "INFO: Le 2 password non corrispondono")
                return redirect('signup')
            #
            if Users.objects.filter(username = in_username).exists():
                messages.error(request, "INFO: Lo username scelto già esiste")
                return redirect('signup')
            #
            try:
                hased_pwd = make_password(password1)

                Users.objects.create(
                    username = in_username,
                    pwd = hased_pwd
                )

                messages.success(request, "INFO: Utente creato con successo")
                return redirect('login')
            except Exception as e:
                print(f"ERRORE: Utente-Create non riuscito: [{e}]")
                messages.error(request, "INFO: Errore nella creazione dell'utente, riprovare più tardi")
    except Exception as e:
        print(f"ERRORE: Utente-SignUp non riuscito: [{e}]")
        messages.error(request, "INFO: Errore nella creazione dell'utente, riprovare più tardi")
    return render(request, TEMPLATE.SIGNUP.value)
# Logout
def logout_view(request: HttpRequest):
    logout(request)
    return redirect("login")
#
# Manual Page Logic
class ManualLogic(View): 

    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'
    JSON_BACK_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\allarmi_soluzioni_backup.json'

    JM = JsonManager(JSON_PATH, CONF_PATH, JSON_BACK_PATH)

    def get(self, request: HttpRequest):

        

        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        
        chosen_language = request.GET.get('language', 'text_it')

        # take all element from the DB table and all JSON key alarm title
        alarm_queryset = AllarmiSoluzioni.objects.all()
        alarm_json_set = set(alarm_file["lista_allarmi"])

        # check the number of element of DB table and JSON key
        alarm_db_count = alarm_queryset.count()
        alarm_json_count = len(alarm_json_set)

        # check the DB element with JSON file and in case upload: Sync JSON -> DB
        if (alarm_db_count == alarm_json_count) and ((cfg_file["db_update"] == 'true') and (cfg_file["json_update"] == 'true')):
            
            messages.info(request, f"INFO: Trovato {alarm_db_count} elementi nel DB")

            if (alarm_db_count == 0 or alarm_json_count == 0):
                messages.info(request, "INFO: Nessun elemento sia nel DB che nel JSON")
                messages.info(request, "INFO: Inizio procedura di recupero")

                cfg_file["db_update"] == 'false'
                cfg_file["json_update"] == 'false'

                alarm_file: dict = self.JM.read_backup_json()
                alarm_file: dict = self.JM.write_alarm_json(alarm_file)

            #
        elif alarm_db_count < alarm_json_count:
            try:
                self.upload_json(alarm_file)

                cfg_file['json_update'] = 'true'
                cfg_file['db_update'] = 'true'

                self.JM.write_conf(cfg_file)

            except Exception as e:
                messages.error(request, f"Errore upload: {e}")
                
            finally:
                messages.info(request, "INFO: Finito...Ricarica la pagina e controlla i risultati...")
        else:
            # caso incoerenza DB > JSON
            alarm_queryset.delete()

            cfg_file['json_update'] = 'false'
            cfg_file['db_update'] = 'false'

            messages.warning(request, "DB resettato. Ricarica la pagina.")

        # Search form
        search_form = SearchAlarmsForm(request.GET)

        alarm_queryset_filtered = None

        if search_form.is_valid():
            search_text = search_form.cleaned_data.get("search_text")

            if search_text:

                request.session['search_text'] = search_text

                # search the string is contained, it's case-insensitive and it performs a partial match
                alarm_queryset_filtered = alarm_queryset.filter(
                    titolo__icontains = search_text
                    ) 
        else:
            search_form = SearchAlarmsForm()

         # Search all DB data - need a name in the html btn and a value to check
        if request.GET.get("all") is not None:
            alarm_queryset_filtered = alarm_queryset

        request.session['chosen_language'] = chosen_language

        # pass the context
        context = {
            'search_form': search_form,
            'alarms_filtered': alarm_queryset_filtered,
            'chosen_language': chosen_language,
            'language_dict': LanguageModel.LANGUAGE_CHOICE.items()
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        #
        title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        img = request.FILES.get("solution_img")
        video = request.FILES.get("solution_video")
        #
        alarm_checkBox = request.POST.get("chk_alarm")
        solution_checkBox = request.POST.get("chk_solution")
        img_checkBox = request.POST.get("chk_img")
        video_checkBox = request.POST.get("chk_video")
        #
        chk_dict = {
            'alarm': alarm_checkBox,
            'solution': solution_checkBox,
            'img': img_checkBox,
            'video': video_checkBox
        }
        #
        action = request.POST.get('action')        
        #
        try:
            if action == 'add':

                if not all([title, solution_text, img, video]):

                    messages.info(request, "INFO: Tutti i campi devo essere riempiti")
                    return redirect(request.path)
                else:
                    self.add_alarm(request, title, solution_text, img, video, alarm_file)
            
            elif action == 'delete':
                self.delete_alarm(request, title, alarm_file)
            
            elif action == 'update': 
                search_title = request.session.get('search_text')

                self.update_alarm(request, search_title, title, solution_text, img, video, chk_dict)
                del request.session['search_text']

            elif action == 'download':
                search_title = request.session.get('search_text')
                chosen_language = request.session.get('chosen_language')

                return self.create_download_pdf(request, search_title, chosen_language)
                # del request.session['search_text']
            #
        except Exception as e:
            messages.error(request, f"ERROR: POST Exception [{e}]")

        return redirect(request.path)
    #
    def upload_json(self, alarm_file: dict):
        alarm_set = set(alarm_file["lista_allarmi"])

        for alarm_name in alarm_set:
            try: 
                temp_obj = AllarmiSoluzioni.objects.get(titolo = alarm_name)
                print(f"Già esiste: [{temp_obj}]")
            except AllarmiSoluzioni.DoesNotExist:
                try:
                    # create the object and auto-save it
                    AllarmiSoluzioni.objects.create(
                        titolo = alarm_name,
                        text_it = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                        text_eng = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                        text_esp = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                        text_de = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                        text_fr = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                        text_dk = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                        text_pt = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                        text_ru = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                        text_pl = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                        text_no = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                        text_se = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                        img = alarm_file["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                        video = alarm_file["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                        )
                    #
                except Exception as e:
                    print(f"Upload from Json Except: [{e}]")
        #
        '''
        STESSA COSA SCRITTA SOPRA FORSE MEGLIO: 

        for alarm_name in alarm_set:
            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=alarm_name,
                defaults={
                    "text_it": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                    "text_eng": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                    "text_esp": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                    "text_de": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                    "text_fr": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                    "text_dk": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                    "text_pt": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                    "text_ru": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                    "text_pl": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                    "text_no": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                    "text_se": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                    "img": alarm_file["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                    "video": alarm_file["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                }
            )
            if created:
                print(f"Creato nuovo allarme: [{obj.titolo}]")
            else:
                print(f"Gia esiste: [{obj.titolo}]")
        '''
    #
    def add_alarm(self, request: HttpRequest, title, solution_text, img, video, alarm_file: dict):
        
        alarm_set = set(alarm_file["lista_allarmi"])
        
        if AllarmiSoluzioni.objects.filter(titolo=title).exists() or title in alarm_set:
            messages.info(request, "Allarme già presente nel DB / JSON")
            return

        translator = Translator()

        translations: dict = {}

        # lingue da tradurre
        languages: dict = {
            "eng": "en",
            "esp": "es",
            "de": "de",
            "fr": "fr",
            "dk": "da",
            "pt": "pt",
            "ru": "ru",
            "pl": "pl",
            "no": "no",
            "se": "sv"
        }

        try:
            for key, lang in languages.items():
                translations[key] = translator.translate(
                    solution_text,
                    src='it',
                    dest=lang
                ).text
        except Exception:
            messages.warning(request, "Errore traduzione automatica")

        # creazione DB-obj
        obj = AllarmiSoluzioni.objects.create(
            titolo=title,
            text_it=solution_text,
            img=img,
            video=video,
            **{f"text_{k}": v for k, v in translations.items()} 
        )

        # translations.items() => (key, value) -> (language, text) == (eng, hello)
        # f"text_{k}" → crea la nuova chiave (text_eng)
        '''
        LA STESSA DI SCRIVERE:
        new_dict = {}

        for k, v in translations.items():
            new_dict[f"text_{k}"] = v
        '''

        print(f"Creato allarme: {obj.titolo}")

        # aggiornamento JSON
        alarm_file["lista_allarmi"][title] = {
            "media": {
                "video": {
                    "nome_file": video,
                    "path_file": str(video)},
                "img": {
                    "nome_file": img,
                    "path_file": str(img)}
            },
            "testo_soluzione": {
                "it": solution_text,
                **translations
            }
        }

        self.JM.write_alarm_json(alarm_file)

        messages.success(request, "Allarme creato correttamente")
    #
    def update_alarm(self, request: HttpRequest, search_title, title, solution_text, img, video, chk_dict: dict):
        
        qs = AllarmiSoluzioni.objects.filter(titolo=search_title)

        if not qs.exists():
            messages.info(request, "L'allarme selezionato non esiste nel DB")
            return

        fields_to_update = {}
        
        # CHECK TITLE - Funziona
        if chk_dict.get("alarm") and title:
            fields_to_update["titolo"] = title

        # TODO: CHECK SOLUTION
        # Criticità: 
        # 1) se non faccio prima la search con il nome giusto la session non mi passa il nome del titolo giusto 
        if chk_dict.get("solution") and solution_text:
            fields_to_update["text_it"] = solution_text
            
            # Traduzioni
            translator = Translator()
            languages = {
                "eng": "en", "esp": "es", "de": "de", "fr": "fr",
                "dk": "da", "pt": "pt", "ru": "ru", "pl": "pl",
                "no": "no", "se": "sv"
            }

            translations = {}

            try:
                for key, lang in languages.items():
                    translations[key] = translator.translate(solution_text, src='it', dest=lang).text
                fields_to_update.update({f"text_{k}": v for k, v in translations.items()})
            except Exception:
                messages.warning(request, "Errore traduzione automatica")

        # CHECK IMG - Funziona
        if chk_dict.get("img") and img:
            fields_to_update["img"] = img

        # CHECK VIDEO - FUnziona
        if chk_dict.get("video") and video:
            fields_to_update["video"] = video

        # Esegui update solo se ci sono campi da aggiornare
        if fields_to_update:
            qs.update(**fields_to_update)
            messages.success(request, "Allarme aggiornato correttamente")
        else:
            messages.info(request, "Nessun campo selezionato o fornito da aggiornare")
    # 
    def delete_alarm(self, request: HttpRequest, title, alarm_file):

        alarm_set = set(alarm_file["lista_allarmi"])

        if title in alarm_set and AllarmiSoluzioni.objects.filter(titolo = title).exists():

            messages.info(request, "Allarme presente sia nel DB e nel JSON")

            try:
                AllarmiSoluzioni.objects.get(titolo = title).delete()

                del alarm_file["lista_allarmi"][title]

                self.JM.write_alarm_json(alarm_file)
            except AllarmiSoluzioni.DoesNotExist:
                messages.info(request, "INFO: L'allarme che si vuole eliminare non è stato trovato nel DB")
            finally:
                messages.info(request, "Allarme eliminato sia nel DB e nel JSON")
        else:
            messages.info(request, "Allarme non presente sia nel DB che nel JSON")
    # 
    def create_download_pdf(self, request: HttpRequest, search_title, chosen_language: str):
        # create ByteStrea Buffer
        buffer = io.BytesIO()

        # create the document
        document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        alarms = AllarmiSoluzioni.objects.get(titolo = search_title)
        
        # list of the elements in the PDF
        elements = []

        # defined styles
        styles = getSampleStyleSheet()

        # custom styles
        custom_styles = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            spaceAfter=10,
            textColor='black'
        )

        # create paragraphs - support HTML tags
        title = Paragraph("Soluzione Allarme", styles['Title'])
        text_title = Paragraph(alarms.titolo, styles['Normal'])
        text_solution = Paragraph(getattr(alarms, chosen_language), custom_styles) # pass chosen__language to obj dinamically
        image = Image(f"project/media/{alarms.img.name}", width=200, height=150)

        # add elements
        elements.append(title)
        elements.append(Spacer(1, 0.2 * mm)) # Aggiunge spazio verticale
        elements.append(text_title)
        elements.append(text_solution)
        elements.append(image)

        # Finish up
        document.build(elements)
        buffer.seek(0)

        # Return
        return FileResponse(buffer, as_attachment=True, filename="Allarme_Soluzioni.pdf")
    # TODO: check why it doesn't work
    def create_download_csv(self, request: HttpRequest, search_title):

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="alarms.csv"'

        writer = csv.writer(response)

        # header
        writer.writerow(["title", "solution"])

        alarms = AllarmiSoluzioni.objects.all()

        for a in alarms:
            writer.writerow([a.titolo, a.text_it])

        return response
    #
#
# Contacts Page Logic
def contacts(request: HttpRequest):
    return render(request, TEMPLATE.CONTACTS.value)
# Account Page Logic
def account(request: HttpRequest):
    return render(request, TEMPLATE.ACCOUNT.value)
# Line Page Logic
def line(request: HttpRequest):
    return render(request, TEMPLATE.LINE.value)