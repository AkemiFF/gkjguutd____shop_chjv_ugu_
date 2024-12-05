# views.py
from django.core.cache import cache
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import *
from .serializers import ProductSerializer

CACHE_TTL = 60 * 5  
class ProductDeleteAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def delete(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        for image in product.images.all():
            image.image.delete()  
            image.delete()        

        product.delete()

        return Response(
            {"message": f"Le produit avec l'ID {product_id} et ses images associées ont été supprimés."},
            status=status.HTTP_200_OK
        )


@method_decorator(cache_page(60 * 5), name='dispatch') 
class TopSellingProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Vérifier si les résultats sont déjà en cache
        cache_key = 'top_selling_products'
        top_products = cache.get(cache_key)

        if not top_products:
            # Si les produits ne sont pas dans le cache, les récupérer depuis la base de données
            top_products = (
                Product.objects
                .annotate(total_sold=Sum('orderitem__quantity'))
                .order_by('-total_sold')[:8]
            )
            # Sérialiser les résultats
            serializer = ProductSerializerAll(top_products, many=True)

            # Mettre en cache les résultats pendant 5 minutes
            cache.set(cache_key, serializer.data, timeout=60 * 5)
        else:
            # Si les produits sont dans le cache, les renvoyer tels quels
             return Response(top_products)

        # Retourner la réponse
        return Response(serializer.data)
    

class RecommendedProductsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        cache_key = 'recommended_products'
        
        top_products = cache.get(cache_key)
        if not top_products:
            top_products = (
                Product.objects
                .annotate(total_reviews=Count('reviews'))  # Compter le nombre d'avis
                .order_by('-total_reviews')[:4]  # Trier par le nombre d'avis, puis prendre les 4 premiers
            )
            serializer = ProductSerializerAll(top_products, many=True)
            # Mettre les résultats dans le cache pendant 5 minutes
            cache.set(cache_key, serializer.data, timeout=60 * 5)
        else:
            # Si les produits sont déjà en cache, les utiliser directement
            return Response(top_products)

        return Response(serializer.data)


@method_decorator(cache_page(60 * 5), name='dispatch') 
class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializerAll
    


class ProductSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')  # Le terme de recherche
        category = request.query_params.get('category')  # Filtre par catégorie
        min_price = request.query_params.get('min_price')  # Filtre par prix minimum
        max_price = request.query_params.get('max_price')  # Filtre par prix maximum

        # Générer une clé de cache dynamique basée sur les paramètres de la requête
        cache_key = f"search:{query}:{category}:{min_price}:{max_price}"
        products = cache.get(cache_key)

        if not products:
            # Filtrer les produits de manière conditionnelle
            products_queryset = Product.objects.all()

            if query:
                products_queryset = products_queryset.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )

            if category:
                products_queryset = products_queryset.filter(category__name__iexact=category)

            if min_price:
                products_queryset = products_queryset.filter(price__gte=min_price)

            if max_price:
                products_queryset = products_queryset.filter(price__lte=max_price)

            # Utiliser select_related ou prefetch_related si nécessaire pour optimiser les relations
            # Exemple : pour une relation ForeignKey ou ManyToMany
            # products_queryset = products_queryset.select_related('category')

            # Appliquer la pagination (optionnelle)
            page_size = int(request.query_params.get('page_size', 10))  # Par défaut, 10 produits par page
            page = int(request.query_params.get('page', 1))  # Numéro de page, par défaut 1
            start = (page - 1) * page_size
            end = page * page_size

            # Appliquer le cache des résultats de la requête
            products = products_queryset[start:end]

            # Sérialiser les produits
            serializer = ProductSerializerAll(products, many=True)

            # Mettre en cache les résultats de la recherche pendant 5 minutes
            cache.set(cache_key, serializer.data, timeout=CACHE_TTL)
        else:
            # Si les résultats sont en cache, les renvoyer directement
            serializer = ProductSerializerAll(products, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 10), name='dispatch') 
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

@method_decorator(cache_page(60 * 5), name='dispatch') 
class CategoryListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@method_decorator(cache_page(60 * 5), name='dispatch') 
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
    permission_classes = [IsAuthenticated] 
    serializer_class = AddProductReviewSerializer
    

    def perform_create(self, serializer):

        serializer.save(user=self.request.user) 