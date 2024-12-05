from django.conf import settings
from django.db import models
from django.db.models import Avg, Count


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    fr_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

        
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0

    def apply_discount(self, percentage):
        if percentage < 0 or percentage > 100:
            raise ValueError("Le pourcentage doit être entre 0 et 100.")
        discount_amount = (self.price * percentage) / 100
        return self.price - discount_amount
    
    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 3

    @property
    def review_count(self):
        return self.reviews.aggregate(Count('id'))['id__count'] or 10


class ProductImage(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.product.name}"



class ProductReview(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    rating = models.PositiveIntegerField(default=5) 
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    helpful_votes = models.PositiveIntegerField(default=0)
    unhelpful_votes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.user.username} ({self.rating}/5)"
    def average_rating(self):
        reviews = self.reviews.all()
        return reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    def review_count(self):
        return self.reviews.count()


class ProductSpecification(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="specifications")
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)  

    class Meta:
        unique_together = ("product", "name")  
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"
