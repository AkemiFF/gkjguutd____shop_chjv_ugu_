# serializers.py
import random

from orders.models import *
from rest_framework import serializers

from .models import *


class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('first_name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        name =validated_data['first_name']
        user = Client.objects.create_user(
            username=name,
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    def validate(self, data):
        if Client.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"message": "Cet e-mail est déjà utilisé."})
        return data
    

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    shipping_addresses = ShippingAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', "shipping_addresses"]
    
class ShippingAddressOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'postal_code', 'country', 'phone_number']



class ClientOrderCreateSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressOrderSerializer(write_only=True)

    class Meta:
        model = Client
        fields = ['username', 'password', 'phone_number', 'address', 'email', 'shipping_address']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extraire les données d'adresse de livraison
        shipping_data = validated_data.pop('shipping_address', None)

        # Générer un nom d'utilisateur unique si le nom est déjà pris
        username = validated_data['username']
        while Client.objects.filter(username=username).exists():
            username = f"{validated_data['username']}_{random.randint(1000, 9999)}"
        validated_data['username'] = username

        # Créer le client avec un nom d'utilisateur unique
        client = Client.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            address=validated_data.get('address'),
            email=validated_data.get('email'),
            is_verified=True  
        )

        # Créer l'adresse de livraison associée, si fournie
        if shipping_data:
            ShippingAddress.objects.create(client=client, **shipping_data)

        return client
    
class UpdateShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'postal_code', 'country', 'phone_number']
        
        
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', "total_price"]
        
class ClientWithOrdersSerializer(serializers.ModelSerializer):
    orders_count = serializers.SerializerMethodField()
    recent_orders = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'date_joined','username', 'email', 'phone_number', 'address', 'orders_count', 'recent_orders']

    def get_orders_count(self, obj):
        return Order.objects.filter(user=obj).count()

    def get_recent_orders(self, obj):
        recent_orders = Order.objects.filter(user=obj).order_by('-created_at')[:5] 
        return OrderSerializer(recent_orders, many=True).data