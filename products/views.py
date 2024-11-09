# views.py
from django.db.models import Q, Sum
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
# views.py
from rest_framework.views import APIView

from .models import Product
from .serializers import *
from .serializers import \
    ProductSerializer  # Assume you have a ProductSerializer


class TopSellingProductsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # Aggregate the total quantity sold for each product
        top_products = (
            Product.objects
            .annotate(total_sold=Sum('orderitem__quantity'))
            .order_by('-total_sold')[:8]
        )
        
        # Serialize the top-selling products
        serializer = ProductSerializerAll(top_products, many=True)
        return Response(serializer.data)



class RecommendedProductsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        top_products = (
            Product.objects
            .annotate(total_reviews=Count('reviews'))  # Compter le nombre d'avis
            .order_by('-total_reviews')[:4]  # Trier par le nombre d'avis, puis prendre les 4 premiers
        )
        
        # Serialize the top-selling products
        serializer = ProductSerializerAll(top_products, many=True)
        return Response(serializer.data)


class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializerAll

class ProductSearchView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        query = request.query_params.get('q', '')  # le terme de recherche
        category = request.query_params.get('category')  # filtre par catégorie
        min_price = request.query_params.get('min_price')  # filtre par prix minimum
        max_price = request.query_params.get('max_price')  # filtre par prix maximum

        # Filtre de recherche avec Q pour combiner plusieurs critères
        products = Product.objects.all()
        
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        
        if category:
            products = products.filter(category__name__iexact=category)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)

        serializer = ProductSerializerAll(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductAdminListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class CategoryCreateUpdateView(APIView):
    permission_classes = [IsAdminUser]
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
    


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductWithSpecSerializer
    lookup_field = 'id'
    
    
    def retrieve(self, request, *args, **kwargs):
        # Récupérer le produit actuel
        product = self.get_object()
        serializer = self.get_serializer(product)

        # Récupérer des produits similaires basés sur la catégorie
        similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

        # Sérialiser les produits similaires
        similar_serializer = ProductSerializerAll(similar_products, many=True)

        # Construire la réponse
        return Response({
            'product': serializer.data,
            'similar_products': similar_serializer.data
        })
        
        
        
class ProductReviewCreateView(generics.CreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = AddProductReviewSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        # Associer automatiquement l'utilisateur authentifié à la critique
        serializer.save(user=self.request.user) 