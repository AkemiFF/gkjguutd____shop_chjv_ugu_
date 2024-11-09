from django.urls import path

from .views import *

urlpatterns = [
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('', UserOrdersView.as_view(), name='user-orders'),
    path('all/', OrderListView.as_view(), name='order-list'),
    path('<int:order_id>/status/', update_order_status, name='update-order-status'),
]
