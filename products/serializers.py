# serializers.py
import json

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'fr_name', 'description', 'created_at', 'updated_at']
        
class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['image',]

    def get_image(self, obj):
        print(obj)
        if isinstance(obj, ProductImage):
            return f"{settings.MEDIA_URL}{obj.image.name}"
        return None

class ProductSerializerAll(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.FloatField( read_only=True)
    review_count = serializers.IntegerField( read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'weight', 'length', 'width', 'height', 'sku', 'category', 'images','average_rating','review_count']

    
User = get_user_model()

class ProductReviewSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user_id', 'username', 'rating', 'title', 'content', 'helpful_votes', 'unhelpful_votes', 'created_at']
        
class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']
      
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name', 'fr_name', 'description']  
      
      


class AddProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['product', 'rating', 'title', 'content']
    
    def create(self, validated_data):

        return ProductReview.objects.create(**validated_data)  
    
class ProductWithSpecSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.FloatField( read_only=True)
    review_count = serializers.IntegerField( read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'weight', 
                  'length', 'width', 'height', 'sku', 'category', 
                  'images', 'specifications', 'average_rating', 'review_count',"reviews"]

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )
    specifications = serializers.ListField(
        write_only=True,
        required=False
    )
    class Meta:
        model = Product
        fields = '__all__'    

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        specifications_data = validated_data.pop('specifications')
        if not images_data:
            raise serializers.ValidationError({"images": "At least one image is required."})
        
        product = Product.objects.create(**validated_data)


        for image in images_data:
            ProductImage.objects.create(product=product, image=image)

        for spec in specifications_data:
            for s in spec:
               ProductSpecification.objects.create(product=product,**s)

        return product