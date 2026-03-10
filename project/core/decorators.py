from django.shortcuts import render, redirect

from django.http import(
    Http404, # raise http404 -> it's an exception 
    HttpRequest, # http request from the client
    HttpResponse, # response from the server
    HttpResponseForbidden # denied access
)

from .models import Users

def check_log_in(func):
    def wrapper(request: HttpRequest, *args, **kwargs):
        user_id = request.session.get('user_id') # taken from the session.user_id

        if user_id is not None:
            try:
                user_obj = Users.objects.get(id=user_id)
                if user_obj.DoesNotExist:
                    raise Http404
                #
                print(f"User Logged In: \nUsername: [{user_obj.username}]")
                return func(request, *args, **kwargs)
            except Exception as e:
                return HttpResponse(f"Something went wrong...")
        else:
            print("Decorator Info: User ID not found... \nThrowing exception...\nRendering Log-In Page...")
            return redirect("login")
    return wrapper
