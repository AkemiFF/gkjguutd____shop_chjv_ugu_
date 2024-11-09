# urls.py
from django.urls import path

from .views import *

urlpatterns = [
    path('register/', ClientCreateView.as_view(), name='client-register'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('send-verification-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('login/', LoginView.as_view(), name='login'),
    path('client/info/', ClientInfoView.as_view(), name='client-info'),
    path('create/order/', ClientOrderCreateView.as_view(), name='create-client'),
    path('update-shipping-info/', UpdateShippingInfoView.as_view(), name='update-shipping-info'),
    path('shipping-info/', GetShippingAddressView.as_view(), name='shipping-info'),
    path('clients/', ClientListView.as_view(), name='client-list'),
]
