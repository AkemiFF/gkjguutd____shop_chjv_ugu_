import hashlib
import hmac
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def verify_signature(secret, payload, signature):
    """Vérifie l'authenticité de la notification."""
    computed_hash = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest().upper()
    return computed_hash == signature

def handle_payment_notification(request):
    """Traite les notifications de paiement de Vanilla Pay."""
    if request.method == "POST":
        secret = os.getenv("KEY_SECRET")
        signature = request.headers.get("VPI-Signature")
        payload = request.body.decode("utf-8")

        if verify_signature(secret, payload, signature):
            # Logique pour gérer les statuts de paiement (SUCCESS, PENDING, FAILED)
            return JsonResponse({"status": "valid"}, status=200)

        return JsonResponse({"status": "invalid"}, status=400)