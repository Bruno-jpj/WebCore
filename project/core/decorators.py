from django.shortcuts import render, redirect

from django.http import(
    Http404, # raise http404 -> it's an exception 
    HttpRequest, # http request from the client
    HttpResponse, # response from the server
    HttpResponseForbidden # denied access
)

from .models import Users

from functools import wraps

'''
def check_log_in(func):
    def wrapper(self, request: HttpRequest, *args, **kwargs):

        user_id = request.session.get('user_id') # taken from the session.user_id

        if not user_id:
            return redirect("login")

        try:
            Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            raise Http404

        return func(self, request, *args, **kwargs)
    return wrapper
#'''

def check_log_in(view):
    """
    Decorator universal: can be used on func or CBV.
    if a CBV, intercept dispatch method.
    """
    if isinstance(view, type):  # if a Class-Based-View
        original_dispatch = view.dispatch

        @wraps(original_dispatch)
        def new_dispatch(self, request: HttpRequest, *args, **kwargs):
            user_id = request.session.get('user_id')
            if not user_id:
                return redirect("login")
            try:
                Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                raise Http404
            return original_dispatch(self, request, *args, **kwargs)

        view.dispatch = new_dispatch
        return view

    else:  # if a def-view
        @wraps(view)
        def wrapper(request: HttpRequest, *args, **kwargs):
            user_id = request.session.get('user_id')
            if not user_id:
                return redirect("login")
            try:
                Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                raise Http404
            return view(request, *args, **kwargs)

        return wrapper