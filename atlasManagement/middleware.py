from datetime import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.shortcuts import redirect
from django.utils.timezone import now
import threading

_user = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user

        if request.user.is_authenticated:
            
            user_sessions = Session.objects.filter(expire_date__gte=now())
            for session in user_sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(request.user.id):
                    
                    if session.session_key != request.session.session_key:
                        session.delete()  
                        
                        request.session['session_warning'] = (
                            "logout_warning|Cerrando la sesión actual debido a un inicio en otro dispositivo."
                        )
                        break


            last_activity = request.session.get('last_activity')
            now_timestamp = datetime.timestamp(datetime.now())

            if last_activity and now_timestamp - last_activity > settings.SESSION_COOKIE_AGE:
                logout(request)
                return redirect('login')
            else:
                request.session['last_activity'] = now_timestamp

        response = self.get_response(request)
        return response

def get_current_authenticated_user():
    try:
        return _user.value
    except AttributeError:
        return None


class UserActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            print(f"Usuario: {request.user.username}, Ruta: {request.path}, Método: {request.method}")
        response = self.get_response(request)
        return response
