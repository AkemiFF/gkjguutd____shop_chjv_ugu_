# views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import *


class ProductAdminListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class CategoryCreateUpdateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # Création d'une catégorie
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        # Modification d'une catégorie existante
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class AddProductReviewView(generics.CreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associe automatiquement l'utilisateur connecté et le produit à l'avis
        product_id = self.kwargs.get('product_id')
        product = generics.get_object_or_404(Product, id=product_id)
        serializer.save(user=self.request.user, product=product)
        
@api_view(['POST'])
def create_product(request):

    
    specs = []  

    if 'specifications' in request.data:
        # specifications could be a list of strings
        specifications_data = request.data.getlist('specifications')  # Get as a list

        # Parse each string in the list
        for spec in specifications_data:
            try:
                spec_dict = json.loads(spec)  # Convert JSON string to dictionary
                specs.append(spec_dict)  # Append the parsed dictionary
            except json.JSONDecodeError:
                return Response({"specifications": "Invalid JSON format for specifications."}, status=status.HTTP_400_BAD_REQUEST)
        request.data['specifications'] = specs

    
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    print(serializer.errors)  # For debugging purposes
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CategoryListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializerAll


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductWithSpecSerializer
    lookup_field = 'id'