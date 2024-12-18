from functools import wraps
from django.shortcuts import redirect

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        print(request.user)
        if request.user:
            return view_func(request, *args, **kwargs)
        else:
            print(f"User not authenticated. Redirecting to login.")
            return redirect('login')
    return _wrapped_view