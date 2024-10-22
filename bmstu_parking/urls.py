from django.urls import path
from django.contrib import admin
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from stocks.views import (
    ParkingListView, ParkingDetailView, ParkingCreateView, ParkingUpdateView, ParkingDeleteView,
    AddParkingToDraftOrderView, AddImageToParkingView,
    OrderListView, OrderDetailView, OrderUpdateView, OrderFormedView, OrderCompleteView, OrderDeleteView,
    DeleteOrderParkingView, UpdateOrderParkingView,
    UserRegisterView, UserUpdateView, LoginView, LogoutView
)

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Паркинги (услуги)
    path('parkings/', ParkingListView.as_view(), name='parking-list'),
    path('parkings/<int:pk>/', ParkingDetailView.as_view(), name='parking-detail'),
    path('parkings/create/', ParkingCreateView.as_view(), name='parking-create'),
    path('parkings/<int:pk>/update/', ParkingUpdateView.as_view(), name='parking-update'),
    path('parkings/<int:pk>/delete/', ParkingDeleteView.as_view(), name='parking-delete'),
    path('parkings/<int:pk>/add-to-draft/', AddParkingToDraftOrderView.as_view(), name='add-parking-to-draft'),
    path('parkings/<int:pk>/add-image/', AddImageToParkingView.as_view(), name='add-image-to-parking'),

    # Заявки
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/form/', OrderFormedView.as_view(), name='order-formed'),
    path('orders/<int:pk>/complete/', OrderCompleteView.as_view(), name='order-complete'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order-delete'),

    # Позиции в заявке (OrderParking)
    path('order-items/<int:order_id>/<int:parking_id>/delete/', DeleteOrderParkingView.as_view(), name='order-parking-delete'),
    path('order-items/<int:order_id>/<int:parking_id>/update/', UpdateOrderParkingView.as_view(), name='order-parking-update'),

    # Пользователи
    path('users/register/', UserRegisterView.as_view(), name='user-register'),
    path('users/update/', UserUpdateView.as_view(), name='user-update'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
]
