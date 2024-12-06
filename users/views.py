# views.py
from cart.models import Cart, CartItem
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
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

    def get(self, request, *args, **kwargs):
        # Définir une clé de cache unique pour la liste des clients
        cache_key = "client_list"

        # Vérifier si les données sont en cache
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Si les données sont en cache, les renvoyer directement
            return Response(cached_data)
        
        # Si les données ne sont pas en cache, les récupérer et mettre en cache
        response = super().get(request, *args, **kwargs)
        
        # Mettre en cache les données pendant 5 minutes
        cache.set(cache_key, response.data, timeout=60 * 5)
        
        return response


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
            
            res = send_email_password(client.email, client.password)
            if res.status_code != 200:
                return Response({"error": "Une erreur s'est produite lors de l'envoi de l'email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            session_key = request.session.session_key
            
            if session_key:
                try:
                    cart = Cart.objects.filter(session=session_key).first()  
                    if cart:
                        cart.user = client
                        cart.save()
                except Cart.DoesNotExist:

                    cart = Cart.objects.create(user=client, session=request.session)
                

            refresh = RefreshToken.for_user(client)
            
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


from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.response import Response

from .models import Client


def send_email_password(email, password):
    try:
        # Préparer le contexte pour le template
        context = {
            'password': password,
        }
        html_content = render_to_string('email-pass.html', context)

        # Créer et envoyer l'email
        email_message = EmailMessage(
            subject='Votre mot de passe',
            body=html_content,
            from_email='noreply@shoplg.com',
            to=[email],
        )
        email_message.content_subtype = 'html'  # Spécifie que le corps est en HTML
        email_message.send(fail_silently=False)

        # Retourner une réponse de succès
        return Response({"message": "Mot de passe envoyé par e-mail"}, status=status.HTTP_200_OK)

    except Exception as e:
        # Gérer les erreurs imprévues
        return Response({"error": f"Erreur lors de l'envoi de l'email : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendPasswordResetEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = "mirado.akemi@gmail.com"
        password = "Fuuuuuuuu**ck"
        res = send_email_password(email,password)
        return res
        
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
        
        # Générer une clé de cache unique pour l'utilisateur
        cache_key = f"client_info_{client.id}"

        # Vérifier si les données sont en cache
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Si les données sont en cache, les renvoyer
            return Response(cached_data)
        
        # Si les données ne sont pas en cache, les récupérer et mettre en cache
        serializer = ClientSerializer(client)
        client_data = serializer.data
        
        # Mettre en cache les données pendant 5 minutes
        cache.set(cache_key, client_data, timeout=60 * 5)
        
        return Response(client_data)


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
    
    

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # Vérifiez que tous les champs sont présents
        if not current_password or not new_password or not confirm_password:
            return Response({"detail": "Tous les champs sont obligatoires."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifiez que le mot de passe actuel est correct
        if not check_password(current_password, user.password):
            return Response({"detail": "Le mot de passe actuel est incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifiez que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            return Response({"detail": "Les nouveaux mots de passe ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        # Modifiez le mot de passe de l'utilisateur
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Mot de passe modifié avec succès."}, status=status.HTTP_200_OK)
    
    
    

# Fonction pour envoyer le code de vérification par email
def send_verification_email(client, verification_code):
    subject = 'Code de vérification pour la réinitialisation de votre mot de passe'
    message = f'Votre code de vérification est : {verification_code}. Il est valable pendant 10 minutes.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client.email])

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    # Vérifier que l'email est fourni
    email = request.data.get('email')
    if not email:
        return Response({'error': 'L\'email est requis.'}, status=400)
    
    # Vérifier si l'email appartient à un client
    try:
        client = Client.objects.get(email=email)
    except Client.DoesNotExist:
        return Response({'error': 'Cet email n\'est pas associé à un compte.'}, status=400)
    
    # Enregistrer le code de vérification dans l'objet client
    client.generate_verification_code()
    verification_code = client.verification_code
    # Envoyer le code de vérification par email
    send_verification_email(client, verification_code)
    
    return Response({'message': 'Un code de vérification a été envoyé à votre email.'})

def get_tokens_for_client(client):
    refresh = RefreshToken.for_user(client)
    access_token = str(refresh.access_token)
    return {
        'access_token': access_token,
        'refresh_token': str(refresh),
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    # Récupérer l'email et le code de vérification dans la requête
    email = request.data.get('email')
    verification_code = request.data.get('verification_code')

    if not email or not verification_code:
        return Response({'error': 'L\'email et le code de vérification sont requis.'}, status=400)

    # Vérifier si le client existe
    try:
        client = Client.objects.get(email=email)
    except Client.DoesNotExist:
        return Response({'error': 'Cet email n\'est pas associé à un compte.'}, status=400)

    # Vérifier si le code de vérification correspond
    if client.verification_code != verification_code:
        return Response({'error': 'Code de vérification invalide.'}, status=400)

    # Vérifier si le code a expiré (10 minutes de validité)
    expiration_time = client.verification_code_sent_at + timedelta(minutes=10)
    if timezone.now() > expiration_time:
        return Response({'error': 'Le code de vérification a expiré.'}, status=400)

    # Si tout est valide, retourner un message de succès
 # Générer les tokens
    tokens = get_tokens_for_client(client)

    # Retourner les tokens
    return Response({
        'message': 'Le code de vérification est valide.',
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
    })
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    new_password = request.data.get('new_password')

    client = request.user 

    # Si tout est valide, mettre à jour le mot de passe
    client.password = make_password(new_password)  # Hash du mot de passe avant de le sauvegarder
    client.save()

    # Réinitialiser le code de vérification après la réinitialisation du mot de passe (optionnel)
    client.verification_code = ''
    client.verification_code_sent_at = None
    client.save()

    # Retourner une réponse de succès
    return Response({'message': 'Mot de passe réinitialisé avec succès.'})