from django.contrib.auth.models import AbstractUser
from django.db import models


class Client(AbstractUser):

    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username
