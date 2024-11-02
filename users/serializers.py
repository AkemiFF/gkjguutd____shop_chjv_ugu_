# serializers.py
import random

from rest_framework import serializers

from .models import Client


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