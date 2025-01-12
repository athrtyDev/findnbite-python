from django.contrib import admin
from django.utils.html import format_html
from .models import Restaurant, Hashtag, RestaurantImage, MenuImage

class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 1

class MenuImageInline(admin.TabularInline):
    model = MenuImage
    extra = 1

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'price_range', 'rating', 'review_count', 'logo_preview')
    list_filter = ('price_range', 'hashtags')
    search_fields = ('name', 'description', 'short_location')
    filter_horizontal = ('hashtags',)
    readonly_fields = ('rating', 'review_count', 'created_at', 'updated_at')
    inlines = [RestaurantImageInline, MenuImageInline]

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = 'Logo'

@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) 