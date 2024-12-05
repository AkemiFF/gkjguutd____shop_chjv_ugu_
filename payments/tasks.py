from cart.models import Cart
from celery import app, shared_task
from orders.models import Order

from .services import *


@shared_task
def test_task(data):
    # Logique de la tâche
    print(f"Received data: {data}")
    return {"status": "success"}




@shared_task
def initiate_cart_payment_task(cart_id, backUrl, frontUrl):
    import time
    start_time = time.time()

    try:
        # Récupérer le panier à partir de l'ID
        cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()
        print(f"Cart query took {time.time() - start_time} seconds")

        if cart is None:
            return {'error': 'Cart not found'}

        # Récupérer les éléments du panier
        cart_items = cart.items.all()
        if not cart_items:
            return {'error': 'Cart is empty'}

        # Calculer le prix total du panier et le convertir en float
        total_price = float(sum(item.get_total_price() for item in cart_items))
        print(f"Total price calculation took {time.time() - start_time} seconds")

        user_id = cart.user.id if cart.user else 0
        ref = f"REF{cart.id}{user_id}T{str(total_price).replace('.', 'P')}"

        payment_data = {
            'montant': total_price,
            'reference': ref,
            'panier': cart.id,
            'devise': "Euro",
            'notif_url': f"{backUrl}/payments/webhook/",
            'redirect_url': f"{frontUrl}/users/cart/order-confirmation"
        }

        # Initier le paiement (appel à une API de paiement)
        # Remplacez `initiate_payment` par l'appel réel de l'API
        payment_response = initiate_payment(payment_data)
        return payment_response

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': str(e)}


@shared_task
def initiate_ref_payment_task(ref, backUrl, frontUrl):
    import time
    start_time = time.time()

    try:
        # Récupérer le panier à partir de l'ID
        order = Order.objects.filter(ref=ref).prefetch_related('order_items__product').first()

        if order is None:
            return {'error': 'order not found'}

        total_price = float(order.get_total_price())    

        payment_data = {
            'montant': total_price,
            'reference': ref,
            'panier': order.id,
            'devise': "Euro",
            'notif_url': f"{backUrl}/payments/webhook/",
            'redirect_url': f"{frontUrl}/users/cart/order-confirmation"
        }

        payment_response = initiate_payment(payment_data)
        return payment_response

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': str(e)}
