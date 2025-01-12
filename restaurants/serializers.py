from rest_framework import serializers
from .models import Restaurant, Hashtag, RestaurantImage, MenuImage

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'

class RestaurantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantImage
        fields = ('image',)

class MenuImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuImage
        fields = ('image',)

class RestaurantSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    images = RestaurantImageSerializer(many=True, read_only=True)
    menu_images = MenuImageSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = '__all__' 