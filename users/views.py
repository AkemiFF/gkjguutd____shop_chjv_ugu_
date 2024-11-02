# views.py
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import ClientCreateSerializer

User = get_user_model()

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

        if user.check_password(password):  # Vérifie le mot de passe
            refresh = RefreshToken.for_user(user)
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