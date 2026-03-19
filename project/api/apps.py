from django.apps import AppConfig


# Django create this file automatically
# it's used to define the apps configuration and can be modified to execute code when the server start and the app read
# you to modify the ready function - it will be executed only the first time the server is started
class ApiConfig(AppConfig):
    name = 'api'

    '''
    def ready(self):
        pass
    '''