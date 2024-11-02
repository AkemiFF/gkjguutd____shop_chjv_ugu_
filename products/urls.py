# urls.py
from django.urls import path

from .views import *

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('list/', ProductAdminListView.as_view(), name='product-list-admin'),
    path('create/', create_product, name='create_product'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:product_id>/review/', AddProductReviewView.as_view(), name='add-product-review'),
    path('category/create/', CategoryCreateUpdateView.as_view(), name='create_category'),
    path('category/update/<int:pk>/', CategoryCreateUpdateView.as_view(), name='update_category'),
]