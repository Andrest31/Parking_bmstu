from django.contrib import admin
from django.urls import path
from parking import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Parking_BMSTU/', views.Parking_BMSTU, name='Parking_BMSTU'),  # Добавьте имя для маршрута
    path('Parking_BMSTU/search/', views.ParkingSearch, name='parking_search'),
    path('info/<int:id>/', views.information, name='information'),
    path('pass/<int:id>/', views.Pass, name='pass'),
    path('add_to_pass/<int:parking_id>/', views.add_to_Pass, name='add_to_pass'),
    path('clear-pass/', views.clear_Pass, name='clear_pass'),
]
