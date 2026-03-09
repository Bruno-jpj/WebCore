from django.contrib import admin
from .models import (
    Macchinari,
    Informazioni,
    Allarmi,
    Componenti,
)

# Register your models here.
admin.register(Macchinari)
admin.register(Informazioni)
admin.register(Allarmi)
admin.register(Componenti)