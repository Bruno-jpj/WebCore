from django.contrib import admin
from .models import (
    ApiKeys,
    ApiRequestLogs,
    CoreRequestLogs
)
# Register your models here.

admin.site.register(ApiKeys)
admin.site.register(ApiRequestLogs)
admin.site.register(CoreRequestLogs)