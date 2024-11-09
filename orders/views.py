from cart.models import Cart
from django.contrib.sessions.models import Session
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

        # Créer la commande
        order_data = {
            'user': request.user.id,
            'total_price': total_price
        }
        serializer = OrderSerializer(data=order_data)
        
        if serializer.is_valid():
            order = serializer.save()
            
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.get_total_price()
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
        orders = Order.objects.select_related('user').prefetch_related('items__product', 'user__shipping_addresses')
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