from django.http import HttpResponseForbidden
from django.conf import settings

# honestly I haven't understood how to use and code middlewares yet; 
# this one was a try and study case but it didn't work
# but if you want to use it you need to put in the settings file

ALLOWED_ADMIN_IPS = ["127.0.0.1"]

class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(settings):
            ip = request.META.get("REMOTE_ADDR")
            if ip not in ALLOWED_ADMIN_IPS:
                return HttpResponseForbidden("Access denied")
        return self.get_response(request)