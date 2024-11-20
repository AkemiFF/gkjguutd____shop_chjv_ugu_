from decouple import config
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

STATIC_USERNAME = config('STATIC_USERNAME')
STATIC_EMAIL = config('STATIC_EMAIL')
STATIC_PASSWORD = config('STATIC_PASSWORD')

# Signal qui s'exécute après la migration de la base de données
@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    # Vérifier si un superutilisateur avec ces informations existe déjà
    User = get_user_model()
    if not User.objects.filter(username=STATIC_USERNAME).exists():
        # Si l'utilisateur n'existe pas, on le crée
        user = User.objects.create_superuser(
            username=STATIC_USERNAME,
            email=STATIC_EMAIL,
            password=STATIC_PASSWORD
        )
        print(f"Superuser created: Username: {STATIC_USERNAME}, Password: {STATIC_PASSWORD}, Email: {STATIC_EMAIL}")
    else:
        print(f"Superuser with username {STATIC_USERNAME} already exists.")
