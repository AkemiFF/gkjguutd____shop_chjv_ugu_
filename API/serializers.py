# serializers.py

from rest_framework import serializers


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class DashboardSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_percentage_change = serializers.FloatField()
    total_orders = serializers.IntegerField()
    orders_percentage_change = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    new_clients_percentage_change = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    conversion_rate_percentage_change = serializers.FloatField()
