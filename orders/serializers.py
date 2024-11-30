from cart.models import Cart
from products.models import *
from rest_framework import serializers
from users.models import *

from .models import Order, OrderItem


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']

class ProductSerializer(serializers.ModelSerializer):
    first_image = ProductImageSerializer(source='images.first', read_only=True)

    class Meta:
        model = Product
        fields = ['id','name', 'description', 'price', 'stock', 'sku', 'first_image']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price'] 
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['user', 'total_price',"reference"]

    def create(self, validated_data):
        return Order.objects.create(**validated_data)
        
class OrderwithItemsSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        return Order.objects.create(**validated_data)
    
class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'postal_code', 'country', 'phone_number']

class ClientSerializer(serializers.ModelSerializer):
    shipping_addresses = ShippingAddressSerializer(many=True)

    class Meta:
        model = Client
        fields = ['username', 'email', 'shipping_addresses']

    
class AdminOrderSerializer(serializers.ModelSerializer):
    user = ClientSerializer()
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'updated_at', 'total_price', 'status', 'items']