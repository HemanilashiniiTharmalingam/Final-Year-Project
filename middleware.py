import time
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class InactivityTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        timeout_duration = 300  # 5 minutes in seconds
        current_time = time.time()

        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity', current_time)
            time_since_last_activity = current_time - last_activity

            if time_since_last_activity > timeout_duration:
                return redirect('register_or_login')

            request.session['last_activity'] = current_time
        return None
