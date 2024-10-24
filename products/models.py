from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)  # Quantité en stock
    image = models.ImageField(
        upload_to="product_images/", null=True, blank=True
    )  # Image du produit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0

    def apply_discount(self, percentage):
        if percentage < 0 or percentage > 100:
            raise ValueError("Le pourcentage doit être entre 0 et 100.")
        discount_amount = (self.price * percentage) / 100
        return self.price - discount_amount
