from django.contrib import admin
from .models import Parking, Order, OrderParking

# Регистрация модели Parking в админ-панели
@admin.register(Parking)
class ParkingAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'place', 'sports', 'open_hour', 'close_hour', 'status']
    search_fields = ['name', 'place']
    list_filter = ['status']
    ordering = ['name']

# Регистрация модели Order в админ-панели
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'planned_date', 'status', 'created_at', 'sumbited_at', 'accepted_at']
    search_fields = ['user__username', 'status']
    list_filter = ['status', 'planned_date']
    ordering = ['created_at']

# Регистрация модели OrderParking в админ-панели
@admin.register(OrderParking)
class OrderParkingAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'parking', 'user', 'quantity']
    search_fields = ['order__id', 'parking__name', 'user__username']
    list_filter = ['order', 'parking']
    ordering = ['order']
