from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Parking, Order, OrderParking, CustomUser

# Сериализатор для модели Parking (услуги)
class ParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = ['id', 'name', 'place', 'sports', 'open_hour', 'close_hour', 'image_card', 'status']
        # Добавление описаний полей для документации Swagger
        extra_kwargs = {
            'id': {'help_text': 'Уникальный идентификатор парковки'},
            'name': {'help_text': 'Название парковки'},
            'place': {'help_text': 'Местоположение парковки'},
            'sports': {'help_text': 'Виды спорта, доступные на парковке'},
            'open_hour': {'help_text': 'Часы открытия парковки'},
            'close_hour': {'help_text': 'Часы закрытия парковки'},
            'image_card': {'help_text': 'URL изображения парковки'},
            'status': {'help_text': 'Статус парковки (активна/неактивна)'},
        }

    def get_fields(self, include=None):
        """
        Возвращает только те поля, которые указаны в include. 
        Если include не задано, возвращает все поля.
        """
        fields = super().get_fields()
        if include:
            fields = {field_name: fields[field_name] for field_name in include if field_name in fields}
        return fields

# Сериализатор для модели Order (заявки)
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'planned_date', 'planned_deadline', 'created_at', 'sumbited_at', 'accepted_at', 'status']
        # Описания полей
        extra_kwargs = {
            'id': {'help_text': 'Уникальный идентификатор заказа'},
            'user': {'help_text': 'Пользователь, сделавший заказ', 'read_only': True},
            'planned_date': {'help_text': 'Запланированная дата заказа'},
            'planned_deadline': {'help_text': 'Запланированный срок выполнения заказа'},
            'created_at': {'help_text': 'Дата и время создания заказа'},
            'sumbited_at': {'help_text': 'Дата и время подачи заказа'},
            'accepted_at': {'help_text': 'Дата и время принятия заказа'},
            'status': {'help_text': 'Статус заказа'},
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class OrderParkingSerializer(serializers.ModelSerializer):
    parking = ParkingSerializer(read_only=True)  # Включаем полную информацию о парковке

    class Meta:
        model = OrderParking
        fields = ['id', 'parking', 'quantity']
        # Описания полей
        extra_kwargs = {
            'id': {'help_text': 'Уникальный идентификатор позиции заказа'},
            'parking': {'help_text': 'Информация о парковке'},
            'quantity': {'help_text': 'Количество мест, забронированных в заказе'},
        }

class OrderDetailSerializer(serializers.ModelSerializer):
    parkings = OrderParkingSerializer(many=True, read_only=True)  # Включаем позиции заказа

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'moderator', 'planned_date', 'planned_deadline', 
            'created_at', 'sumbited_at', 'accepted_at', 'status', 'completed_at', 'rejected_at',
            'parkings'  # Включаем список парковок в заказе
        ]
        # Описания полей
        extra_kwargs = {
            'id': {'help_text': 'Уникальный идентификатор заказа'},
            'user': {'help_text': 'Пользователь, сделавший заказ', 'read_only': True},
            'moderator': {'help_text': 'Модератор, проверивший заказ'},
            'planned_date': {'help_text': 'Запланированная дата заказа'},
            'planned_deadline': {'help_text': 'Запланированный срок выполнения заказа'},
            'created_at': {'help_text': 'Дата и время создания заказа'},
            'sumbited_at': {'help_text': 'Дата и время подачи заказа'},
            'accepted_at': {'help_text': 'Дата и время принятия заказа'},
            'status': {'help_text': 'Статус заказа'},
            'completed_at': {'help_text': 'Дата и время завершения заказа'},
            'rejected_at': {'help_text': 'Дата и время отклонения заказа'},
            'parkings': {'help_text': 'Список парковок в заказе'},
        }

# Сериализатор для модели User (пользователи)
class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(help_text='Имя пользователя для входа')
    password = serializers.CharField(write_only=True, help_text='Пароль для входа')
