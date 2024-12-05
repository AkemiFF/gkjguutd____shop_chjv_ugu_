import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            return JsonResponse({"error": "Une erreur serveur est survenue. Merci de réessayer."}, status=500)
        return response
