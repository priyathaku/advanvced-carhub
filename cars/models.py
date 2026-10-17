from django.db import models
from django.contrib.auth.models import User


class Car(models.Model):
    FUEL_CHOICES = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Hybrid', 'Hybrid'),
    ]

    TRANSMISSION_CHOICES = [
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('Dual-Clutch', 'Dual-Clutch'),
    ]

    BODY_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('Sedan', 'Sedan'),
        ('Coupe', 'Coupe'),
        ('Convertible', 'Convertible'),
        ('Sports Car', 'Sports Car'),
    ]

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, default='', help_text="Static image path or external URL")
    gallery_images = models.JSONField(blank=True, default=list, help_text="List of additional image URLs for gallery")
    year = models.PositiveIntegerField(default=2024)
    fuel_type = models.CharField(max_length=50, choices=FUEL_CHOICES, default='Petrol')
    transmission = models.CharField(max_length=50, choices=TRANSMISSION_CHOICES, default='Automatic')
    mileage = models.PositiveIntegerField(default=0, help_text="Mileage in km")
    engine = models.CharField(max_length=100, default='4.0L V8 Biturbo')
    horsepower = models.PositiveIntegerField(default=500, help_text="Horsepower in HP")
    seating_capacity = models.PositiveIntegerField(default=5)
    body_type = models.CharField(max_length=50, choices=BODY_TYPE_CHOICES, default='Coupe')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.brand} {self.name} ({self.year})"

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        if self.image_url:
            return self.image_url
        return '/static/images/car1.png'

    def get_all_images(self):
        images = [self.get_image_url()]
        if self.gallery_images and isinstance(self.gallery_images, list):
            for img in self.gallery_images:
                if img and img not in images:
                    images.append(img)
        return images

    @property
    def formatted_price(self):
        try:
            return f"${int(self.price):,}"
        except (ValueError, TypeError):
            return f"${self.price}"


# Model for Contact Messages
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, default='General Inquiry')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


# Model for Test Drive Requests
class TestDriveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='test_drives')
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=50)
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Test Drive: {self.name} - {self.car} ({self.preferred_date})"


# Model for Saved Favorites / Wishlist
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites')
    session_key = models.CharField(max_length=60, blank=True, null=True)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        ident = self.user.username if self.user else f"Session:{self.session_key[:8]}"
        return f"{ident} -> {self.car}"
