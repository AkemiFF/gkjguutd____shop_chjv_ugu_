from django.contrib.sessions.models import Session

from .models import Cart


def migrate_cart_to_user(session_cart, user):
    session_cart.user = user
    session_cart.session = None
    session_cart.save()

def get_cart_for_anonymous_user(session_key):
    try:
        session = Session.objects.get(session_key=session_key)
        cart = Cart.objects.get(session=session)
        return cart
    except Session.DoesNotExist:
        return None
