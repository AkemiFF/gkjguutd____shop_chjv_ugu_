
from django.shortcuts import get_object_or_404
from products.models import Product
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Cart, CartItem
from .utils import get_cart_for_anonymous_user


def get_cart_for_anonymous_user(session_key):
    """Fonction utilitaire pour obtenir le panier d'un utilisateur anonyme basé sur la session, avec cache."""
    if not session_key:
        return None 

    cart = Cart.objects.filter(session_id=session_key, user=None).first()
    return cart

@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart(request):
    """Récupérer le panier de l'utilisateur, ou créer un nouveau panier pour les utilisateurs anonymes."""
    # Générer une clé de cache unique en fonction de l'utilisateur ou de la session
    if request.user.is_authenticated:
        cart_key = f"cart_user_{request.user.id}"  # Clé pour utilisateur authentifié
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key or request.session.save()
        cart_key = f"cart_session_{session_key}"  # Clé pour utilisateur anonyme
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
        # Mettre en cache les données du panier pendant 5 minutes (300 secondes)

        return Response(cart_data, status=status.HTTP_200_OK)

    return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart_connected_user(request):
    """Récupérer le panier de l'utilisateur connecté ou créer un panier pour les utilisateurs anonymes."""

    # Générer une clé de cache unique en fonction de l'utilisateur ou de la session
    if request.user.is_authenticated:
        cart_key = f"cart_user_{request.user.id}"
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key or request.session.save()
        cart_key = f"cart_session_{session_key}"
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
                    "image_url": item.product.images.first().image.url if item.product.images.exists() else None
                }
                for item in cart.items.all()
            ]
        }

        product_ids_in_cart = [item.product.id for item in cart.items.all()]
        categories_in_cart = cart.items.values_list('product__category', flat=True).distinct()

        recommended_products = (
            Product.objects.filter(category__in=categories_in_cart)
            .exclude(id__in=product_ids_in_cart)
            .distinct()[:4]
        )

        recommended_data = [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "average_rating": product.average_rating,
                "review_count": product.review_count,
                "description": product.description,
                "images": [{"image": image.image.url} for image in product.images.all()] if product.images.exists() else []
            }
            for product in recommended_products
        ]

        cart_data["recommended_products"] = recommended_data
        cart_data["cart_id"] = cart.id


        return Response(cart_data, status=status.HTTP_200_OK)

    return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart_session_user(request):
    """Récupérer le panier de l'utilisateur, ou créer un nouveau panier pour les utilisateurs anonymes."""
    
    # Récupérer le panier en fonction de l'utilisateur connecté ou de la session anonyme
   
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
                    "image_url": item.product.images.first().image.url if item.product.images.exists() else None
                }
                for item in cart.items.all()
            ]
        }

        # Récupérer les catégories des produits dans le panier pour les recommandations
        product_ids_in_cart = [item.product.id for item in cart.items.all()]
        categories_in_cart = cart.items.values_list('product__category', flat=True).distinct()
        
        # Rechercher 4 produits recommandés dans les mêmes catégories, exclure ceux déjà dans le panier
        recommended_products = (
            Product.objects.filter(category__in=categories_in_cart)
            .exclude(id__in=product_ids_in_cart)
            .distinct()[:4]
        )

        # Sérialiser les produits recommandés
        recommended_data = [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "average_rating": product.average_rating,
                "review_count": product.review_count,
                "description": product.description,
                "images": [{"image": image.image.url} for image in product.images.all()] if product.images.exists() else []
            }
            for product in recommended_products
        ]

        # Ajouter les recommandations aux données de réponse
        cart_data["recommended_products"] = recommended_data
        cart_data["cart_id"] = cart.id
        return Response(cart_data, status=status.HTTP_200_OK)

    return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([ AllowAny])
def test_session(request):
    if not request.session.session_key:
        request.session.save()  

    return Response({"message": "Produit ajouté au panier."}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
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
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_key, user=None)

    # Ajouter ou mettre à jour l'élément dans le panier
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    
    product_ids_in_cart = [item.product.id for item in cart.items.all()]
    categories_in_cart = cart.items.values_list('product__category', flat=True).distinct()

    recommended_products = (
        Product.objects.filter(category__in=categories_in_cart)
        .exclude(id__in=product_ids_in_cart)
        .distinct()[:4]
    )

    recommended_data = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "average_rating": product.average_rating,
            "review_count": product.review_count,
            "description": product.description,
            "images": [{"image": image.image.url} for image in product.images.all()] if product.images.exists() else []
        }
        for product in recommended_products
    ]

   

    return Response({"message": "Produit ajouté au panier."}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
def remove_from_cart(request, product_id):
    """Retirer un produit du panier."""
    session_key = request.session.session_key
    cart = get_cart_for_anonymous_user(session_key)

    if not cart:
        return Response({"message": "No cart found."}, status=status.HTTP_404_NOT_FOUND)

    # Définir la clé de cache en fonction de l'utilisateur ou de la session
    if request.user.is_authenticated:
        cart_key = f"cart_user_{request.user.id}"
    else:
        cart_key = f"cart_session_{session_key}"

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
        # Vérifier si l'utilisateur est authentifié ou anonyme
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:            
            session_key = request.session.session_key
            cart = Cart.objects.get(session_id=session_key, user=None)

        # Vérifier si l'élément existe dans le panier
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        # Réduire la quantité ou supprimer l'élément du panier
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            message = "La quantité du produit a été réduite."
        else:
            cart_item.delete()
            message = "Le produit a été supprimé du panier."

        # Mettre à jour le cache après la modification du panier
     

        return Response({"message": message}, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        return Response({"error": "Panier introuvable pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_cart_item(request):
    """Supprimer un produit du panier."""
    product_id = request.data.get('product_id')

    if not product_id:
        return Response({"error": "Le product_id est requis."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Récupérer le panier de l'utilisateur connecté ou anonyme
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            session_key = request.session.session_key
            cart = Cart.objects.get(session_id=session_key, user=None)

        # Récupérer l'élément du panier correspondant au produit
        cart_item = get_object_or_404(CartItem.objects.select_related('product'), cart=cart, product_id=product_id)

        # Supprimer l'élément du panier
        cart_item.delete()

        return Response({"message": "Le produit a été supprimé du panier."}, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        return Response({"error": "Panier introuvable pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)