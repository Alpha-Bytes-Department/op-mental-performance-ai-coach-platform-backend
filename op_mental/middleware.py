from django.http import JsonResponse
from rest_framework import status

class ForceLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.force_logout_required:
            # The user needs to be logged out. We clear the flag and return a 401 response.
            request.user.force_logout_required = False
            request.user.save()
            return JsonResponse(
                {'detail': 'You have been logged out from another device.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = self.get_response(request)
        return response
