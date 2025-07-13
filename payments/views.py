import hashlib
import hmac
import json
import os
import time

from asgiref.sync import sync_to_async
from cart.models import Cart
from celery.result import AsyncResult
from decouple import config
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import create_payment_intent
from .tasks import *

frontUrl = config("FROND_URL")
backUrl = config("BACK_URL")
# frontUrl = 'https://shoplg.online'

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import create_payment_intent


@csrf_exempt
def get_stripe_client_secret(request):
    data = json.loads(request.body)
    amount = data.get('amount')
    reference = data.get('reference')
    intent = create_payment_intent(amount_eur=amount, reference=reference)
    return JsonResponse(intent)

@csrf_exempt
def create_checkout_session(request):
    data = json.loads(request.body)
    amount = data.get('amount')
    reference = data.get('reference')
    frontUrl = data.get('frontUrl')
    session = create_payment_intent(
        amount_eur=amount,
        reference=reference,
        return_url=f"{frontUrl}/success"
    )
    return JsonResponse(session)

class CheckOrderPayment(APIView):
    permission_classes = [AllowAny]
    def get(self, request, reference):
        try:
            order = Order.objects.get(reference=reference)
            if order.is_paid:
                return Response({'is_paid': True}, status=status.HTTP_200_OK)
            else:
                # Wait for 3 seconds before retrying
                time.sleep(3)
                # Check again
                order.refresh_from_db()  # Refresh the order instance from the database
                if order.is_paid:
                    return Response({'is_paid': True}, status=status.HTTP_200_OK)
                else:
                    return Response({'is_paid': False}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@csrf_exempt
def init_payment(request):
    """Expose l'API pour initier un paiement."""
    if request.method == "POST":
        try:
            # Charger le corps de la requête JSON
            body = json.loads(request.body)
            payment_data = create_payment_intent(body)
            return JsonResponse(payment_data)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def init_cart_payment(request):
    """Expose l'API pour initier un paiement."""
    if request.method == "POST":
        try:
            start_time = time.time()

            # Charger le corps de la requête JSON
            body = json.loads(request.body)
            cart_id = body.get('id')

            # Vérifier si l'ID du panier est fourni
            if not cart_id:
                return JsonResponse({'error': 'Cart ID is required'}, status=400)

            # Essayer de récupérer le panier
            cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()
            print(f"Cart query took {time.time() - start_time} seconds")

            if cart is None:
                return JsonResponse({'error': 'Cart not found'}, status=404)

            # Récupérer les éléments du panier
            cart_items = cart.items.all()
            if not cart_items:
                return JsonResponse({'error': 'Cart is empty'}, status=400)

            # Calculer le prix total du panier et le convertir en float
            total_price = float(sum(item.get_total_price() for item in cart_items))
            print(f"Total price calculation took {time.time() - start_time} seconds")

            user_id = cart.user.id if cart.user else 0
            ref = f"REF{cart.id}{user_id}T{str(total_price).replace('.', 'P')}"

            paymentData = {
                'montant': total_price,
                'reference':ref,
                'panier': cart.id,
                'devise': "Euro",
                'notif_url': f"{backUrl}/payments/webhook/",
                'redirect_url': f"{frontUrl}/users/cart/order-confirmation"
            }

            # Initier le paiement
            payment_data = create_payment_intent(paymentData)
            return JsonResponse(payment_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)



    
@csrf_exempt  
def handle_payment_notification_test(request):
    if request.method == "POST":
        try:
            # Récupérer la clé secrète
            key_secret = getattr(settings, "KEY_SECRET", None)
            if not key_secret:
                return JsonResponse({"error": "KEY_SECRET not configured"}, status=500)

            # Récupérer la signature et le corps brut de la requête
            signature = request.headers.get("VPI-Signature")
            payload = request.body.decode("utf-8")  # Corps brut de la requête

            if not signature:
                return JsonResponse({"error": "Missing signature in headers"}, status=400)

            # Calculer la signature pour vérifier l'authenticité
            computed_hash = hmac.new(
                key_secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256
            ).hexdigest().upper()

            if computed_hash != signature:
                return JsonResponse({"error": "Invalid signature"}, status=401)

            # Analyse du JSON dans le corps
            data = json.loads(payload)
            reference_vpi = data.get("reference_VPI")
            reference = data.get("reference")
            panier = data.get("panier")
            montant = data.get("montant")
            etat = data.get("etat")

            # Logique de traitement en fonction de l'état
            if etat == "SUCCESS":
                print(f"Paiement réussi : Référence {reference}, Montant {montant}")
            elif etat == "FAILED":
                print(f"Paiement échoué : Référence {reference}")
            elif etat == "PENDING":
                print(f"Paiement en attente : Référence {reference}")
            else:
                return JsonResponse({"error": "Unknown state"}, status=400)

            # Réponse à envoyer à Vanilla Pay
            return JsonResponse({"message": "Notification reçue et traitée."}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Erreur inattendue : {e}")
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)




@csrf_exempt
def init_cart_payment_stripe(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            cart_id = body.get('id')
            if not cart_id:
                return JsonResponse({'error': 'Cart ID is required'}, status=400)

            cart = Cart.objects.filter(id=cart_id).first()
            if not cart:
                return JsonResponse({'error': 'Cart not found'}, status=404)

            task = initiate_cart_payment_task.delay(cart_id, frontUrl)
            return JsonResponse({'task_id': task.id, 'message': 'Payment initiation started'}, status=202)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
async def init_ref_payment(request):
    """Expose l'API pour initier un paiement de manière asynchrone."""
    if request.method == "POST":
        try:
            start_time = time.time()

            # Charger le corps de la requête JSON
            body = json.loads(request.body)
            ref = body.get('ref')

            # Vérifier si l'ID du panier est fourni
            if not ref:
                return JsonResponse({'error': 'Reference is required'}, status=400)

            task = initiate_ref_payment_task.delay(ref, backUrl, frontUrl)         
           
            return JsonResponse({'task_id': task.id, 'message': 'Payment initiation started'}, status=202)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
   

@csrf_exempt
def get_task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'error': 'Task ID is required'}, status=400)

    # Récupérer l'état de la tâche
    task_result = AsyncResult(task_id)
    if task_result.state == 'SUCCESS':
        return JsonResponse({'state': task_result.state, 'result': task_result.result})
    elif task_result.state == 'FAILURE':
        return JsonResponse({'state': task_result.state, 'error': str(task_result.result)})
    else:
        return JsonResponse({'state': task_result.state})
