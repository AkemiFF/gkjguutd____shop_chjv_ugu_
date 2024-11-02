# cart/urls.py
from django.urls import include, path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import admin_login

urlpatterns = [
    path('', include('users.urls')),
    path('cart/', include('cart.urls')),
    path('product/', include('products.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/admin/login/', admin_login, name='admin_login'),
]
