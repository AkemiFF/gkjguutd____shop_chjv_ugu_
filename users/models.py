import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Client(AbstractUser):
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    is_manager = models.BooleanField(_("is manager"), default=False)
    def __str__(self):
        return self.username

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.verification_code_sent_at = timezone.now()
        self.save()

    def is_verification_code_valid(self):
        expiration_time = self.verification_code_sent_at + timedelta(minutes=10)
        return timezone.now() <= expiration_time
    
    
class ShippingAddress(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shipping_addresses')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.client.username}, {self.city}, {self.country}"

    class Meta:
        verbose_name = "Shipping Address"
        verbose_name_plural = "Shipping Addresses"