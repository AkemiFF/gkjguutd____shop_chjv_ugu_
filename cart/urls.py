from django.urls import path

from .views import *

urlpatterns = [
    path('', get_cart_connected_user, name='get_cart'),
    path('session/', get_cart_session_user, name='get_cart'),
    path('add/', add_to_cart, name='add_to_cart'),
    path('decrease/', decrease_cart_item, name='add_to_cart'),
    path('remove/item/', remove_cart_item, name='remove_cart_item'),
    path('remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
]
