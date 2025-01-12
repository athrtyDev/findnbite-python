from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Restaurant(models.Model):
    PRICE_CHOICES = [
        ('$', '$'),
        ('$$', '$$'),
        ('$$$', '$$$'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    short_location = models.CharField(max_length=200)
    description = models.TextField()
    price_range = models.CharField(max_length=3, choices=PRICE_CHOICES)
    url = models.URLField()
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    hashtags = models.ManyToManyField(Hashtag, blank=True)
    logo = models.ImageField(upload_to='restaurants/logos/', blank=True, null=True)
    rating = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RestaurantImage(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='restaurants/images/')

class MenuImage(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='restaurants/menus/') 