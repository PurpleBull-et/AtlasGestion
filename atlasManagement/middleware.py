import threading

_user = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        response = self.get_response(request)
        return response

def get_current_authenticated_user():
    try:
        return _user.value
    except AttributeError:
        return None