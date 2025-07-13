import stripe
from cart.models import Cart
from celery import shared_task
from django.conf import settings
from orders.models import Order

from .services import create_payment_intent


@shared_task
def initiate_cart_payment_task(cart_id, frontUrl):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()
    if not cart:
        return {'error': 'Cart not found'}
    print(frontUrl)
    total_price = float(sum(item.get_total_price() for item in cart.items.all()))
    user_id = cart.user.id if cart.user else 0
    reference = f"REF{cart.id}{user_id}T{str(total_price).replace('.', 'P')}"

    # Créer PaymentIntent ou Checkout
    return create_payment_intent(
        amount_eur=total_price,
        reference=reference,
        return_url=f"{frontUrl}/users/cart/order-confirmation"
    )


@shared_task
def initiate_ref_payment_task(ref, frontUrl):
    order = Order.objects.filter(reference=ref).prefetch_related('items__product').first()
    if not order:
        return {'error': 'Order not found'}

    total_price = float(order.get_total_price())
    result = create_payment_intent(
        amount_eur=total_price,
        reference=ref,
        return_url=f"{frontUrl}/orders/{ref}/confirmation"
    )
    return result
