from django.contrib import admin
from .models import (
    Macchinari,
    Informazioni,
    AllarmiSoluzioni,
    DjangoSession,
    DjangoAdminLog,
    Users
)

# Register your models here.
admin.site.register(Macchinari)
admin.site.register(Informazioni)
admin.site.register(AllarmiSoluzioni)

admin.site.register(DjangoAdminLog)
admin.site.register(DjangoSession)

admin.site.register(Users)