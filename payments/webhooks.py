import hashlib
import hmac
import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order


def verify_signature(secret, payload, signature):
    """Vérifie l'authenticité de la notification."""
    computed_hash = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest().upper()

    return computed_hash == signature

@csrf_exempt
def handle_payment_notification(request):
    """Traite les notifications de paiement de Vanilla Pay."""
    if request.method == "POST":
        secret = os.getenv("KEY_SECRET")
        signature = request.headers.get("VPI-Signature")
        payload = request.body.decode("utf-8")
        
        if verify_signature(secret, payload, signature.upper()):
            try:
                payload_json = json.loads(payload)
     
                if payload_json.get('etat') == 'SUCCESS':
                    try:
                        ref = payload_json.get('reference')
                        print(f"current reference : {ref}")
              
                        order = Order.objects.get(reference=ref)
                        print(f"Order for ref {ref} is :  {order}")

                        order.is_paid = True
                        
                        order.save()
                        

                    except Order.DoesNotExist:
                        print("La commande avec cette référence n'existe pas.")
                    except Exception as e:
                        print(f"Une erreur s'est produite : {e}")
                    
            except json.JSONDecodeError as e:
                print(f"Erreur lors de la conversion du payload : {e}")
            return JsonResponse({"status": "valid"}, status=200)

        return JsonResponse({"status": "invalid"}, status=400)