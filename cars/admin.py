from django.contrib import admin
from .models import Car, ContactMessage, TestDriveRequest, Favorite


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'year', 'price', 'fuel_type', 'transmission', 'is_featured')
    list_filter = ('brand', 'body_type', 'fuel_type', 'transmission', 'is_featured', 'year')
    search_fields = ('name', 'brand', 'engine')
    list_editable = ('price', 'is_featured')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)


@admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'car', 'phone', 'preferred_date', 'preferred_time', 'status', 'created_at')
    list_filter = ('status', 'preferred_date')
    search_fields = ('name', 'email', 'phone', 'car__name', 'car__brand')
    list_editable = ('status',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('car', 'user', 'session_key', 'created_at')
    list_filter = ('created_at',)
