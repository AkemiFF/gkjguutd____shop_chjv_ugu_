import json

from cart.models import Cart
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import generate_token, initiate_payment

frontUrl = 'https://shoplg.online'
# frontUrl = 'https://shoplg.online'
def get_token(request):
    """Expose l'API pour récupérer un token."""
    token_data = generate_token()  # Appelle la fonction utilitaire
    return JsonResponse(token_data)

@csrf_exempt
def init_payment(request):
    """Expose l'API pour initier un paiement."""
    if request.method == "POST":
        try:
            # Charger le corps de la requête JSON
            body = json.loads(request.body)
            payment_data = initiate_payment(body)
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
            # Charger le corps de la requête JSON
            body = json.loads(request.body)
            cart_id = body.get('id')

            # Vérifier si l'ID du panier est fourni
            if not cart_id:
                return JsonResponse({'error': 'Cart ID is required'}, status=400)

            # Essayer de récupérer le panier
            cart = Cart.objects.filter(id=cart_id).first()
            if cart is None:
                return JsonResponse({'error': 'Cart not found'}, status=404)

            # Récupérer les éléments du panier
            cart_items = cart.items.all()
            if not cart_items:
                return JsonResponse({'error': 'Cart is empty'}, status=400)

            # Calculer le prix total du panier et le convertir en float
            total_price = float(sum(item.get_total_price() for item in cart_items))
            user_id = cart.user.id if cart.user else 0
            paymentData = {
                'montant': total_price,
                'reference': f"REF{cart.id}{user_id}T{total_price}",
                'panier': cart.id,
                'devise': "Euro",
                'notif_url': f"{frontUrl}/users/cart/api/response/",
                'redirect_url': f"{frontUrl}/users/profil/"
            }

            # Initier le paiement
            payment_data = initiate_payment(paymentData)
            return JsonResponse(payment_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    
