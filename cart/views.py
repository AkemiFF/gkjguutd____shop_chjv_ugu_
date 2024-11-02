from django.shortcuts import get_object_or_404
from products.models import Product
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .utils import get_cart_for_anonymous_user


def get_cart_for_anonymous_user(session_key):
    """Fonction utilitaire pour obtenir le panier d'un utilisateur anonyme basé sur la session."""
    if not session_key:
        return None
    return Cart.objects.filter(session_id=session_key, user=None).first()

@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart(request):
    """Récupérer le panier de l'utilisateur, ou créer un nouveau panier pour les utilisateurs anonymes."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key or request.session.save()
        cart = get_cart_for_anonymous_user(session_key)

    if cart:
        # Convertir le panier en format JSON
        cart_data = {
            "items": [
                {
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "total_price": item.get_total_price()
                }
                for item in cart.items.all()
            ]
        }
        return Response(cart_data, status=status.HTTP_200_OK)

    return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([ AllowAny])
def get_cart_connected_user(request):
    """Récupérer le panier de l'utilisateur, ou créer un nouveau panier pour les utilisateurs anonymes."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key or request.session.save()
        cart = get_cart_for_anonymous_user(session_key)

    if cart:
        cart_data = {
            "items": [
                {
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price": item.product.price,
                    "description": item.product.description,
                    "total_price": item.get_total_price(),
                    "image_url": item.product.images.first().image.url
                }
                for item in cart.items.all()
            ]
        }
        return Response(cart_data, status=status.HTTP_200_OK)

    return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([ AllowAny])
def test_session(request):
    if not request.session.session_key:
        request.session.save()  

    print(request.session.session_key)
    return Response({"message": "Produit ajouté au panier."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([ AllowAny])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    

    # Validation de l'identifiant produit
    if not product_id:
        return Response({"error": "Le produit est requis."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = get_object_or_404(Product, id=product_id)
    except Exception as e:
        return Response({"error": "Produit non trouvé."}, status=status.HTTP_404_NOT_FOUND)

    # Vérification de la quantité
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return Response({"error": "La quantité doit être supérieure à zéro."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"error": "Quantité invalide."}, status=status.HTTP_400_BAD_REQUEST)

    # Création ou récupération du panier
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, defaults={'session': None})
    else:
        if not request.session.session_key:
            request.session.save()  

        session_key =request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_key, user=None)

    # Ajouter ou mettre à jour l'élément dans le panier
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    return Response({"message": "Produit ajouté au panier."}, status=status.HTTP_201_CREATED)
@api_view(['DELETE'])
def remove_from_cart(request, product_id):
    """Retirer un produit du panier."""
    session_key = request.session.session_key
    cart = get_cart_for_anonymous_user(session_key)

    if not cart:
        return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.delete()
        return Response({"message": "Product removed from cart."}, status=status.HTTP_204_NO_CONTENT)
    except CartItem.DoesNotExist:
        return Response({"message": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def decrease_cart_item(request):
    """Réduire la quantité d'un produit dans le panier ou le supprimer si la quantité est 1."""
    product_id = request.data.get('product_id')

    if not product_id:
        return Response({"error": "Le product_id est requis."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:            
            session_key =request.session.session_key
            cart  = Cart.objects.get(session_id=session_key, user=None)

        # Récupérer l'élément du panier correspondant au produit
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        # Réduire la quantité ou supprimer l'élément du panier
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            return Response({"message": "La quantité du produit a été réduite."}, status=status.HTTP_200_OK)
        else:
            cart_item.delete()
            return Response({"message": "Le produit a été supprimé du panier."}, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        return Response({"error": "Panier introuvable pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_cart_item(request):
    """Réduire la quantité d'un produit dans le panier ou le supprimer si la quantité est 1."""
    product_id = request.data.get('product_id')

    if not product_id:
        return Response({"error": "Le product_id est requis."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:            
            session_key =request.session.session_key
            cart  = Cart.objects.get(session_id=session_key, user=None)

        # Récupérer l'élément du panier correspondant au produit
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        
        cart_item.delete()
        return Response({"message": "Le produit a été supprimé du panier."}, status=status.HTTP_200_OK)
    
    except Cart.DoesNotExist:
        return Response({"error": "Panier introuvable pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)