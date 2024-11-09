# views.py
from cart.models import Cart, CartItem
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import *


class ClientListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Client.objects.all()
    serializer_class = ClientWithOrdersSerializer
    

class GetShippingAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Récupérer l'adresse de livraison de l'utilisateur connecté
            shipping_address = ShippingAddress.objects.get(client=request.user)
        except ShippingAddress.DoesNotExist:
            # Si l'adresse de livraison n'existe pas pour cet utilisateur
            return Response(
                {"error": "Adresse de livraison non trouvée."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Sérialiser l'adresse de livraison et la retourner
        serializer = ShippingAddressSerializer(shipping_address)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
User = get_user_model()

class ClientOrderCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClientOrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Sauvegarde du client
            client = serializer.save()

            # Lier le panier de session à l'utilisateur créé
            session_key = request.session.session_key
            
            if session_key:
                try:
                    # Récupérer le panier associé à la session (s'il existe)
                    cart = Cart.objects.get(session=session_key)
                    cart.user = client  # Associer le panier à l'utilisateur
                    cart.save()
                except Cart.DoesNotExist:

                    cart = Cart.objects.create(user=client, session=request.session)
                
            # Créer un token de rafraîchissement et d'accès pour l'utilisateur
            refresh = RefreshToken.for_user(client)

            # Retourner les informations nécessaires dans la réponse
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': client.id,
                    'username': client.username,
                    'email': client.email,
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'phone_number': client.phone_number,
                    'address': client.address,
                    'is_verified': client.is_verified,
                }
            }, status=status.HTTP_201_CREATED)
        
        # En cas d'erreur de validation, retournez les erreurs du serializer
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ClientCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = ClientCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            send_email_code(serializer.instance.email)
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_email_code(email):
    try:
            user = Client.objects.get(email=email)
            user.generate_verification_code()

            send_mail(
                'Votre code de vérification',
                f'Votre code de vérification est {user.verification_code}',
                'noreply@votreapp.com',
                [user.email],
                fail_silently=False,
            )
            return Response({"message": "Code de vérification envoyé par e-mail"}, status=status.HTTP_200_OK)
    except Client.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND)
        
class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        send_email_code(email)
        
class VerifyCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = Client.objects.get(email=email)
            if user.is_verified:
                return Response({"message": "User already verified."}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(user.verification_code) == code and user.is_verification_code_valid():
                user.is_verified = True
                user.verification_code = None  
                user.save()
                return Response({"message": "User verified successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)
        
        except Client.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)




class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Authentification basée sur l'e-mail
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)

            # Vérification du panier de session
            session_cart = Cart.objects.filter(session=request.session.session_key).first()

            if session_cart:
                # Vérifier si l'utilisateur a déjà un panier
                user_cart = Cart.objects.filter(user=user).first()

                if user_cart:
                    # Transférer les articles du panier de session vers le panier de l'utilisateur
                    for item in session_cart.items.all():
                        CartItem.objects.update_or_create(
                            cart=user_cart,
                            product=item.product,
                            defaults={'quantity': item.quantity}
                        )
                    session_cart.delete()
                else:
                    # Lier le panier de session directement à l'utilisateur
                    session_cart.user = user
                    session_cart.save()
                
                
            # Réponse de connexion avec les informations utilisateur
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'address': user.address,
                    'is_verified': user.is_verified,
                }
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

class ClientInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user  # Récupère l'utilisateur authentifié
        serializer = ClientSerializer(client)
        return Response(serializer.data)



class UpdateShippingInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Essayer de récupérer ou de créer l'adresse de livraison
        try:
            shipping_address = ShippingAddress.objects.get(client=request.user)
            address_exists = True
        except ShippingAddress.DoesNotExist:
            shipping_address = ShippingAddress(client=request.user)  # Créer une nouvelle instance sans la sauvegarder encore
            address_exists = False

        # Valider et créer ou mettre à jour les données
        serializer = UpdateShippingAddressSerializer(shipping_address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Enregistre ou met à jour l'adresse de livraison
            status_code = status.HTTP_200_OK if address_exists else status.HTTP_201_CREATED
            return Response(serializer.data, status=status_code)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)