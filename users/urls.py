# urls.py
from django.urls import path

from .views import *

urlpatterns = [
    path('register/', ClientCreateView.as_view(), name='client-register'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('send-verification-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('login/', LoginView.as_view(), name='login'),
]
