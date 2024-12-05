from django.urls import path

from .views import *
from .webhooks import handle_payment_notification

urlpatterns = [
    path("get-token/", get_token, name="get_token"),
    path("init-payment/", init_payment, name="init_payment"),
    path("init-cart-payment/", init_cart_payment, name="init_cart_payment"),
    path("webhook/", handle_payment_notification, name="payment_notification"),    
    path("check/<str:reference>/", CheckOrderPayment.as_view(), name="check_payment"),
    path("test/", init_test, name="init_test"),
    path("async-cart-pay/", init_cart_payment2, name="init_test"),
    path("async-ref-pay/", init_ref_payment, name="init_test"),
    path("get-task-status/", get_task_status, name="get_task_status"),
    # path("api/response/pay", views.handle_payment_notification, name="handle_payment_notification"),
]
