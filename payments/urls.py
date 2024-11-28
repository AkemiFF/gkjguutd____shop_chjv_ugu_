from django.urls import path

from .views import *
from .webhooks import handle_payment_notification

urlpatterns = [
    path("get-token/", get_token, name="get_token"),
    path("init-payment/", init_payment, name="init_payment"),
    path("init-cart-payment/", init_cart_payment, name="init_cart_payment"),
    path("webhook/", handle_payment_notification, name="payment_notification"),
]
