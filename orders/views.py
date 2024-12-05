from cart.models import Cart
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import *


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Vérifier le panier et calculer le prix total
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session=session_key).first()

        if not cart:
            return Response({"error": "Le panier est vide."}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum(item.get_total_price() for item in cart.items.all())

        
        reference = request.data.get('reference')  # Obtenir la référence depuis request.data

        # Créer les données de commande
        order_data = {
            'user': request.user.id,
            'total_price': total_price,
            'reference': reference  # Utiliser la référence extraite de request.data
        }

        serializer = OrderSerializer(data=order_data)
        
        if serializer.is_valid():
            order = serializer.save()
            
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.get_total_price(),
                )

            cart.delete()

            return Response({'id': order.id}, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderwithItemsSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
class OrderListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Order.objects.filter(is_paid=True).select_related('user').prefetch_related('items__product', 'user__shipping_addresses')
        serializer = AdminOrderSerializer(orders, many=True)
        return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_order_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OrderDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        # Récupérer la commande
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Construire les détails de la commande
        order_details = {
            "orderNumber": order.reference or f"Order-{order.id}",
            "orderDate": order.created_at.strftime("%d %B %Y"),
            "totalAmount": float(order.total_price),
            "deliveryAddress": "123 Rue Principale, 75000 Paris, France",
            "estimatedDelivery": "30 octobre - 2 novembre 2023",
            
        }
        order_min = {
            "status": order.status,
            "is_paid": order.is_paid,   
            "reference": order.reference,   
        }
        # Construire les détails des produits
        ordered_items = [
            {
                "id": item.id,
                "name": item.product.name,
                "price": float(item.price),
                "quantity": item.quantity,
                "image": (
                    item.product.images.first().image.url
                    if item.product.images.exists()
                    else "/placeholder.svg?height=80&width=80"
                    ),    
                 }
            for item in order.items.all()
        ]

        return Response({
            "orderDetails": order_details,
            "orderedItems": ordered_items,
            "order":order_min,
        })