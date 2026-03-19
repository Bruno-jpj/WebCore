from django.contrib import admin
from .models import (
    ApiKeys,
    ApiRequestLogs,
    CoreRequestLogs
)
# Register you models here will display them in the Admin WebPage and you can perform some actions directly there without coding
admin.site.register(ApiKeys)
admin.site.register(ApiRequestLogs)
admin.site.register(CoreRequestLogs)