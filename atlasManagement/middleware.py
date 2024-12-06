import threading
from datetime import datetime
from django.conf import settings
from django.contrib.auth import logout

_user = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user

        if request.user.is_authenticated:
            
            last_activity = request.session.get('last_activity')
            now = datetime.timestamp(datetime.now())


            if last_activity and now - last_activity > settings.SESSION_COOKIE_AGE:
                logout(request) 
            else:
                
                request.session['last_activity'] = now

        response = self.get_response(request)
        return response

def get_current_authenticated_user():
    try:
        return _user.value
    except AttributeError:
        return None