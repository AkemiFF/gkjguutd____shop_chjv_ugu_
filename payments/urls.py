from django.urls import path

from .views import *
from .webhooks import handle_payment_notification

urlpatterns = [
    path('stripe/client-secret/', get_stripe_client_secret, name='stripe_client_secret'),
    path('stripe/create-checkout/', create_checkout_session, name='stripe_checkout'),
    path("init-payment/", init_payment, name="init_payment"),
    path("init-cart-payment/", init_cart_payment, name="init_cart_payment"),
    path("webhook/", handle_payment_notification, name="stripe_webhook"),    
    path("check/<str:reference>/", CheckOrderPayment.as_view(), name="check_payment"),
    path("async-cart-pay/", init_cart_payment_stripe, name="init_init_cart_payment_stripe"),
    path("async-ref-pay/", init_ref_payment, name="init_ref_payment"),
    path("get-task-status/", get_task_status, name="get_task_status"),
    # path("api/response/pay", views.handle_payment_notification, name="handle_payment_notification"),
]
