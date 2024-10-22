from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Parking, Order, OrderParking

# Сериализатор для модели Parking (услуги)
class ParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = ['id', 'name', 'place', 'sports', 'open_hour', 'close_hour', 'image_card', 'status']

# Сериализатор для модели Order (заявки)
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'planned_date', 'planned_deadline', 'created_at', 'sumbited_at', 'accepted_at', 'status']

    # Поле user не должно быть передано с клиента, поэтому исключаем его
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
class OrderParkingSerializer(serializers.ModelSerializer):
    parking = ParkingSerializer(read_only=True)  # Включаем полную информацию о парковке

    class Meta:
        model = OrderParking
        fields = ['id', 'parking', 'quantity']


class OrderDetailSerializer(serializers.ModelSerializer):
    parkings = OrderParkingSerializer(many=True, read_only=True)  # Включаем позиции заказа

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'moderator', 'planned_date', 'planned_deadline', 
            'created_at', 'sumbited_at', 'accepted_at', 'status', 'completed_at', 'rejected_at',
            'parkings'  # Включаем список парковок в заказе
        ]

# Сериализатор для модели User (пользователи)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}  # Пароль не будет возвращаться в ответе
        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Хешируем пароль перед сохранением
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

