from django.contrib import admin
from django.urls import path
from parking import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', views.hello, name='hello'),  # Добавьте имя для маршрута
    path('info/<int:id>/', views.information, name='information'),
    path('cart/<int:id>/', views.cart, name='cart'),
    path('add_to_cart/<int:parking_id>/', views.add_to_cart, name='add_to_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
]
