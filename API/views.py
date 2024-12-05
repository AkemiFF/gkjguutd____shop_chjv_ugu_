
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, F, Sum
from django.utils import timezone
from orders.models import *
from orders.models import Order
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Client

from .serializers import *


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    today = timezone.now()
    first_day_of_last_month = today.replace(day=1) - timezone.timedelta(days=1)
    first_day_of_last_month = first_day_of_last_month.replace(day=1)
    last_day_of_last_month = today.replace(day=1) - timezone.timedelta(days=1)

    last_week_start = today - timezone.timedelta(weeks=1)
    first_day_of_this_month = today.replace(day=1)

    # Calculer le chiffre d'affaires total
        
    # Calcul du revenu total pour ce mois
    total_revenue = Order.objects.filter(
        is_paid=True,
        created_at__month=first_day_of_this_month.month
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Calcul du revenu total pour le mois dernier
    total_revenue_last_month = Order.objects.filter(
        is_paid=True,
        created_at__month=first_day_of_last_month.month
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Pourcentage de changement de revenu
    revenue_percentage_change = (
        ((total_revenue - total_revenue_last_month) / total_revenue_last_month * 100)
        if total_revenue_last_month > 0 else 0
    )

    # Nombre total de commandes pour ce mois
    total_orders = Order.objects.filter(
        is_paid=True,
        created_at__gte=first_day_of_this_month
    ).count()

    # Nombre total de commandes depuis la semaine dernière
    total_orders_last_week = Order.objects.filter(
        is_paid=True,
        created_at__gte=last_week_start
    ).count()
    orders_percentage_change = total_orders - total_orders_last_week

    # Nombre total de clients et nouveaux clients depuis le mois dernier
    total_clients = Client.objects.count()
    new_clients_last_month = Client.objects.filter(date_joined__gte=first_day_of_last_month).count()
    new_clients_percentage_change = ((total_clients - new_clients_last_month) / new_clients_last_month * 100) if new_clients_last_month > 0 else 0

    # Taux de conversion et son pourcentage par rapport au mois dernier
    total_visits = 1000  # Exemples, vous devrez remplacer cela par vos données réelles sur les visites
    conversion_rate = (total_orders / total_visits) * 100 if total_visits > 0 else 0
    total_orders_last_month = Order.objects.filter( is_paid=True,created_at__month=first_day_of_last_month.month).count()
    conversion_rate_last_month = (total_orders_last_month / total_visits) * 100 if total_visits > 0 else 0
    conversion_rate_percentage_change = conversion_rate - conversion_rate_last_month

    # Retourner les données dans un format structuré
    data = {
        'total_revenue': total_revenue,
        'revenue_percentage_change': revenue_percentage_change,
        'total_orders': total_orders,
        'orders_percentage_change': orders_percentage_change,
        'total_clients': total_clients,
        'new_clients_percentage_change': new_clients_percentage_change,
        'conversion_rate': conversion_rate,
        'conversion_rate_percentage_change': conversion_rate_percentage_change,
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    serializer = AdminLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            # Create tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'is_admin': user.is_superuser,
                'is_manager': user.is_manager,
                'token': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                },
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
        
        return Response({'detail': 'Invalid credentials or not an admin.'}, status=status.HTTP_403_FORBIDDEN)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAdminUser])
def sales_and_orders_data(request):
    # Date du début de l'année actuelle
    today = timezone.now()
    first_day_of_year = today.replace(month=1, day=1)
    
    # Initialisation d'un tableau pour les mois de l'année
    sales_data = []

    for month in range(1, 13):  # 1 pour Jan, 2 pour Feb, ..., 12 pour Dec
        # Calculer le début et la fin du mois courant
        start_of_month = today.replace(month=month, day=1)
        end_of_month = start_of_month.replace(month=month % 12 + 1, day=1) - timezone.timedelta(days=1) if month < 12 else today
        
        # Calculer le total des ventes et des commandes pour ce mois
        monthly_sales = Order.objects.filter( is_paid=True,created_at__gte=start_of_month, created_at__lte=end_of_month).aggregate(Sum('total_price'))['total_price__sum'] or 0
        monthly_orders = Order.objects.filter( is_paid=True,created_at__gte=start_of_month, created_at__lte=end_of_month).count()

        # Ajouter ces données au tableau
        sales_data.append({
            'name': start_of_month.strftime('%b'),  # Ex: Jan, Feb, Mar...
            'sales': monthly_sales,
            'orders': monthly_orders,
            'visitors': 50,  # Remplacer par vos données réelles de visites si disponibles
        })

    return Response(sales_data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([AllowAny])
def create_contact(request):
    serializer = ContactUsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Message envoyé avec succès."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_contacts(request):
    # Clé de cache unique pour la liste des contacts
    cache_key = "all_contacts"

    # Vérifier si les données sont en cache
    cached_data = cache.get(cache_key)

    if cached_data:
        # Si les données sont en cache, les renvoyer
        return Response(cached_data, status=status.HTTP_200_OK)

    # Si les données ne sont pas en cache, les récupérer depuis la base de données
    contacts = ContactUs.objects.all()
    serializer = ContactUsAllSerializer(contacts, many=True)
    
    # Mettre les données dans le cache pendant 5 minutes
    cache.set(cache_key, serializer.data, timeout=60 * 5)

    return Response(serializer.data, status=status.HTTP_200_OK)

# class AnalyticsDataView(APIView):
#     permission_classes = [AllowAny]
#     def get(self, request, *args, **kwargs):
#         try:
#             sessions = get_analytics_data()
#             return Response({"sessions": sessions}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class TopSellingProductView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, *args, **kwargs):
        # Filtrer sur les produits vendus uniquement dans les commandes payées
        top_products = (
            OrderItem.objects.filter(order__is_paid=True)  # Filtrer par commandes payées
            .values("product__id", "product__name")
            .annotate(
                total_sales=Sum("quantity"),  # Nombre total vendu
                total_revenue=Sum(F("quantity") * F("price")),  # Revenu total généré
            )
            .order_by("-total_sales")[:3]  # Limiter aux 3 meilleurs produits
        )

        if top_products:
            data = [
                {
                    "product_id": product["product__id"],
                    "product_name": product["product__name"],
                    "total_sales": product["total_sales"],
                    "total_revenue": product["total_revenue"],
                }
                for product in top_products
            ]
        else:
            data = {"message": "Aucun produit vendu pour l'instant."}

        return Response(data)
    
    
class RecentOrdersView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        # Obtenir les 5 commandes les plus récentes
        recent_orders = (
            Order.objects.filter(is_paid=True)
            .select_related("user")
            .order_by("-created_at")[:5]
        )
        # Construire la réponse
        data = [
            {
                "id": order.reference,
                "customer": order.user.username,
                "total": order.total_price,
                "status": order.status,
            }
            for order in recent_orders
        ]

        return Response(data)