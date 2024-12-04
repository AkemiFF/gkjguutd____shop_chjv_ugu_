# cart/urls.py
from django.urls import include, path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import *

urlpatterns = [
    path('', include('users.urls')),
    path('cart/', include('cart.urls')),
    path('product/', include('products.urls')),
    path('order/', include('orders.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/admin/login/', admin_login, name='admin_login'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('dashboard/sales-orders/', sales_and_orders_data, name='sales-orders-data'),
    path('contact-us/', create_contact, name='create_contact'),
    path('contacts/', get_all_contacts, name='get_all_contacts'),
    path("top-selling-product/", TopSellingProductView.as_view(), name="top-selling-product"),
    path("recent-orders/", RecentOrdersView.as_view(), name="recent-orders"),

    # path('test/', AnalyticsDataView.as_view(), name='get_al'),
]
