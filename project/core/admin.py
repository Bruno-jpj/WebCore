from django.contrib import admin
from .models import (
    Macchinari,
    Informazioni,
    AllarmiSoluzioni,
    Componenti,
    DatiCilindri,
    DatiManutenzione,
    DatiMotori,
    DatiRiduttori,
    Manutenzioni,
    DjangoSession,
    DjangoAdminLog,
    Users
)

# Register your models here.
admin.site.register(Macchinari)
admin.site.register(Informazioni)
admin.site.register(AllarmiSoluzioni)
admin.site.register(Componenti)
admin.site.register(DatiCilindri)
admin.site.register(DatiMotori)
admin.site.register(DatiManutenzione)
admin.site.register(DatiRiduttori)
admin.site.register(Manutenzioni)

admin.site.register(DjangoAdminLog)
admin.site.register(DjangoSession)

admin.site.register(Users)