from rest_framework import generics, status
from rest_framework.response import Response
from .models import Parking, Order, OrderParking
from rest_framework.permissions import AllowAny
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from .serializers import *
from django.utils.timezone import now
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import models
from minio.error import MinioException
from minio.error import S3Error
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from datetime import datetime
import logging
import minio.error
print(dir(minio.error))
from django.contrib.auth import logout
from .serializers import LoginSerializer
from minio import Minio
from minio_storage.storage import MinioStorage
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from stocks.models import CustomUser  # или откуда у вас импортируется CustomUser
from stocks.permissions import IsAdmin, IsManager
import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
# Connect to our Redis instance
session_storage = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

def method_permission_classes(classes):
        def decorator(func):
            def decorated_func(self, *args, **kwargs):
                self.permission_classes = classes        
                self.check_permissions(self.request)
                return func(self, *args, **kwargs)
            return decorated_func
        return decorator


logger = logging.getLogger(__name__)

minio_client = Minio(
            'localhost:9000',  # Change to your MinIO endpoint
            access_key='minio',
            secret_key='minio124',
            secure=False  # Change to True if using HTTPS
        )
class CustomMinioStorage(MinioStorage):
    def __init__(self, *args, **kwargs):
        # Initialize MinIO client
        minio_client = Minio(
            'localhost:9000',  # Change to your MinIO endpoint
            access_key='minio',
            secret_key='minio124',
            secure=False  # Change to True if using HTTPS
        )
        bucket_name = 'my-media-bucket'  # Use your bucket name
        super().__init__(minio_client=minio_client, bucket_name=bucket_name, *args, **kwargs)




# GET список услуг с фильтрацией
class ParkingListView(generics.ListAPIView):
    serializer_class = ParkingSerializer
    ordering_fields = ['name', 'open_hour']

    @swagger_auto_schema(
        operation_description="Получить список всех парковок",
        responses={
            200: openapi.Response(
                description="Список парковок",
                schema=ParkingSerializer(many=True),
            )
        },
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Фильтр по имени", type=openapi.TYPE_STRING),
            openapi.Parameter('place', openapi.IN_QUERY, description="Фильтр по месту", type=openapi.TYPE_STRING),
            openapi.Parameter('sports', openapi.IN_QUERY, description="Фильтр по видам спорта", type=openapi.TYPE_STRING),
            openapi.Parameter('open_hour', openapi.IN_QUERY, description="Фильтр по времени открытия", type=openapi.TYPE_STRING),
            openapi.Parameter('close_hour', openapi.IN_QUERY, description="Фильтр по времени закрытия", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Фильтр по статусу (True/False)", type=openapi.TYPE_BOOLEAN),
        ]
    )
    @method_permission_classes([AllowAny])  # Доступ для всех
    def get_queryset(self):
        draft_order = Order.objects.filter(user=self.request.user, status='draft').first()
        queryset = Parking.objects.all()

        # Получаем параметры фильтрации из запроса
        name = self.request.query_params.get('name')
        place = self.request.query_params.get('place')
        sports = self.request.query_params.get('sports')
        open_hour = self.request.query_params.get('open_hour')
        close_hour = self.request.query_params.get('close_hour')
        status = self.request.query_params.get('status')

        # Фильтрация по параметрам
        if name:
            queryset = queryset.filter(name__icontains=name)
        if place:
            queryset = queryset.filter(place__icontains=place)
        if sports:
            queryset = queryset.filter(sports__icontains=sports)
        if open_hour:
            queryset = queryset.filter(open_hour__gte=open_hour)
        if close_hour:
            queryset = queryset.filter(close_hour__lte=close_hour)
        if status is not None:  # Проверка на None для BooleanField
            queryset = queryset.filter(status=status)

        if draft_order:
            queryset = queryset.annotate(
                service_count=Count('orderparking', filter=Q(orderparking__order=draft_order))
            )

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)  # Получаем базовый ответ с парковками
        draft_order = Order.objects.filter(user=self.request.user, status='draft').first()

        # Считаем количество услуг в черновике
        services_in_draft_order = OrderParking.objects.filter(order=draft_order).aggregate(total=Count('id'))['total'] if draft_order else 0

        # Добавляем в ответ id черновика заявки пользователя и количество услуг в черновике
        response.data = {
            'draft_order_id': draft_order.id if draft_order else None,
            'services_in_draft_order': services_in_draft_order,
            'parkings': response.data
        }

        return Response(response.data)

# Получение деталей парковки
class ParkingDetailView(generics.RetrieveAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

    @swagger_auto_schema(
        operation_description="Получить информацию о парковке по ID",
        responses={
            200: openapi.Response(
                description="Детали парковки",
                schema=ParkingSerializer,
            ),
            404: "Парковка не найдена"
        }
    )
    @method_permission_classes([AllowAny])  # Доступ для всех
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# Создание парковки
class ParkingCreateView(generics.CreateAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

    @swagger_auto_schema(
        operation_description="Добавление новой услуги",
        request_body=ParkingSerializer,
        responses={
            201: openapi.Response('Услуга успешно добавлена', ParkingSerializer),
            400: "Некорректные данные"
        }
    )
    @method_permission_classes([IsAdmin | IsManager])  # Доступ только для админов и менеджеров
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

# Обновление парковки
class ParkingUpdateView(generics.UpdateAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

    @swagger_auto_schema(
        operation_description="Изменение услуги",
        request_body=ParkingSerializer,
        responses={
            200: openapi.Response('Услуга успешно изменена', ParkingSerializer),
            400: "Некорректные данные",
            404: "Парковка не найдена"
        }
    )
    @method_permission_classes([IsAdmin | IsManager])  # Доступ только для админов и менеджеров
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

# Удаление парковки
class ParkingDeleteView(generics.DestroyAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

    @swagger_auto_schema(
        operation_description="Удаление услуги по ID",
        responses={
            204: "Услуга успешно удалена",
            404: "Парковка не найдена"
        }
    )
    @method_permission_classes([IsAdmin | IsManager])  # Доступ только для админов и менеджеров
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

# Добавление парковки в черновик
class AddParkingToDraftOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Добавить парковку в черновик заказа",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Количество'),
            },
        ),
        responses={
            201: openapi.Response('Парковка добавлена в черновик', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успешном добавлении'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Обновлённое количество')
            })),
            404: "Парковка не найдена"
        }
    )
    @method_permission_classes([IsAuthenticated])  # Доступ только для авторизованных
    def post(self, request, pk):
        try:
            parking = Parking.objects.get(pk=pk)
        except Parking.DoesNotExist:
            return Response({"detail": "Парковка не найдена."}, status=status.HTTP_404_NOT_FOUND)

        order, created = Order.objects.get_or_create(
            user=request.user,
            status='draft',
            defaults={'created_at': timezone.now()}
        )

        order_parking, order_parking_created = OrderParking.objects.get_or_create(
            order=order,
            parking=parking,
            user=request.user,
            defaults={'quantity': 1}
        )

        if not order_parking_created:
            order_parking.quantity += 1
            order_parking.save()

        return Response({
            "detail": "Парковка добавлена в черновик.",
            "quantity": order_parking.quantity
        }, status=status.HTTP_201_CREATED)

# Добавление изображения к парковке
class AddImageToParkingView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Добавить изображение к парковке",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image': openapi.Schema(type=openapi.TYPE_FILE, description='Изображение парковки'),
            },
        ),
        responses={
            200: openapi.Response('Изображение успешно загружено', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успешной загрузке'),
                'image_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL загруженного изображения')
            })),
            400: "Нет изображения в запросе",
            404: "Парковка не найдена"
        }
    )
    @method_permission_classes([IsAuthenticated])  # Доступ только для авторизованных
    def post(self, request, pk):
        parking = get_object_or_404(Parking, pk=pk)
        uploaded_file = request.FILES.get('image')

        if not uploaded_file:
            return Response({"detail": "Нет загруженного изображения."}, status=status.HTTP_400_BAD_REQUEST)

        if parking.image_card:
            try:
                minio_client.remove_object(settings.MINIO_STORAGE_MEDIA_BUCKET_NAME, parking.image_card)
                logger.info(f"Удалено старое изображение: {parking.image_card}")
            except S3Error as e:
                logger.error(f"Ошибка удаления старого изображения: {e}")
                return Response({"detail": f"Ошибка удаления старого изображения: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        file_name = f"parkings/{parking.id}/{timezone.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        try:
            minio_client.put_object(
                settings.MINIO_STORAGE_MEDIA_BUCKET_NAME,
                file_name,
                uploaded_file.file,
                uploaded_file.size,
                content_type=uploaded_file.content_type
            )
            logger.info(f"Загружено новое изображение: {file_name}")
        except S3Error as e:
            logger.error(f"Ошибка загрузки изображения: {e}")
            return Response({"detail": f"Ошибка загрузки изображения: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        parking.image_card = file_name
        parking.save()

        return Response({
            "detail": "Изображение загружено успешно.", 
            "image_url": minio_client.presigned_get_object(settings.MINIO_STORAGE_MEDIA_BUCKET_NAME, file_name)
        }, status=status.HTTP_200_OK)


# GET список заявок с фильтрацией
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # Доступ всем пользователям

    # Используем @swagger_auto_schema непосредственно над методом get()
    @swagger_auto_schema(
        operation_description="Получить список заявок с возможностью фильтрации по дате и статусу",
        manual_parameters=[
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description="Дата начала фильтрации (в формате YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description="Дата окончания фильтрации (в формате YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Статус заявки (например, 'formed', 'completed', 'rejected')",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: openapi.Response(
                description="Список заявок",
                schema=OrderSerializer(many=True),
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Order.objects.exclude(status='deleted').exclude(status='draft')  # Не показывать удаленные и черновики
        
        # Получение параметров фильтрации
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        status = self.request.query_params.get('status', None)

        # Фильтрация по дате
        if start_date:
            try:
                queryset = queryset.filter(created_at__gte=datetime.fromisoformat(start_date))
            except ValueError:
                pass  # Обработка ошибки, если формат даты неправильный
        if end_date:
            try:
                queryset = queryset.filter(created_at__lte=datetime.fromisoformat(end_date))
            except ValueError:
                pass  # Обработка ошибки, если формат даты неправильный
        if status:
            queryset = queryset.filter(status=status)

        return queryset

# GET одна заявка
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    queryset = Order.objects.all()
    permission_classes = [AllowAny]  # Доступ всем пользователям

    @swagger_auto_schema(
        operation_description="Получить информацию о заявке по ID",
        responses={
            200: openapi.Response(
                description="Детали заявки",
                schema=OrderDetailSerializer,
            ),
            404: "Заявка не найдена"
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            order = self.get_object()  # Получаем заказ по переданному ID
            response_data = self.get_serializer(order).data  # Сериализуем данные заказа
            return Response(response_data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            raise NotFound("Заказ не найден")


# PUT изменение полей заявки
class OrderUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Доступ только для авторизованных пользователей

    @swagger_auto_schema(
        operation_description="Обновить поля заявки",
        request_body=OrderSerializer,
        responses={
            200: openapi.Response(description="Заявка успешно обновлена", schema=OrderSerializer),
            404: "Заявка не найдена"
        }
    )
    @csrf_exempt
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

# PUT сформировать заявку (создателем)
class OrderFormedView(APIView):
    permission_classes = [IsAuthenticated]  # Доступ только для авторизованных пользователей

    @swagger_auto_schema(
        operation_description="Сформировать заявку",
        responses={
            200: openapi.Response(description="Заявка успешно сформирована"),
            400: "Некорректные данные или статус заявки",
            404: "Заявка не найдена"
        }
    )
    def put(self, request, *args, **kwargs):
        # Получаем заявку по её ID
        order = get_object_or_404(Order, id=kwargs.get('pk'))

        # Проверяем, что заявка находится в статусе 'черновик'
        if order.status == 'draft':
            # Проверка обязательных полей
            if not order.client_name:
                return Response({'error': 'ФИО клиента не заполнено'}, status=status.HTTP_400_BAD_REQUEST)
            if not order.license_plate:
                return Response({'error': 'Гос. номер не заполнен'}, status=status.HTTP_400_BAD_REQUEST)
            if not order.planned_deadline:
                return Response({'error': 'Дата планируемого завершения не указана'}, status=status.HTTP_400_BAD_REQUEST)

            # Если все обязательные поля заполнены, меняем статус на 'сформирован'
            order.status = 'formed'
            order.sumbited_at = timezone.now()
            order.save()

            return Response({'status': 'Заявка сформирована'}, status=status.HTTP_200_OK)

        # Если заявка не в статусе черновика, возвращаем ошибку
        return Response({'error': 'Заявка не может быть сформирована'}, status=status.HTTP_400_BAD_REQUEST)

# PUT завершить/отклонить заявку (модератором)
class OrderCompleteView(APIView):
    permission_classes = [IsAdmin]  # Доступ только для модераторов

    @swagger_auto_schema(
        operation_description="Завершить или отклонить заявку",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['completed', 'rejected'], description='Новый статус заявки'),
            },
        ),
        responses={
            200: openapi.Response(description="Заявка успешно завершена или отклонена"),
            400: "Некорректный статус или статус заявки",
            404: "Заявка не найдена"
        }
    )
    def put(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')  # Получаем ID заказа из URL
        user = request.user  # Получаем текущего пользователя (модератора)
        
        # Получаем заявку или возвращаем 404, если она не найдена
        order = get_object_or_404(Order, id=order_id)

        # Проверяем, что статус заявки — 'formed', иначе возвращаем ошибку
        if order.status != 'formed':
            return Response({'error': 'Завершить или отклонить можно только сформированную заявку.'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем статус из тела запроса
        new_status = request.data.get('status')

        # Проверяем, что статус корректен
        if new_status not in ['completed', 'rejected']:
            return Response({'error': 'Некорректный статус. Должен быть "completed" или "rejected".'}, status=status.HTTP_400_BAD_REQUEST)

        # Рассчитываем общее количество мест в заявке
        total_quantity = OrderParking.objects.filter(order=order).aggregate(total=models.Sum('quantity'))['total']
        total_quantity = total_quantity if total_quantity else 0  # Убедимся, что если заявка пустая, результат будет 0

        # Обновляем поле total_quantity в заявке
        order.total_quantity = total_quantity
        order.save()

        # Обрабатываем статус "завершена"
        if new_status == 'completed':
            if order.status != 'completed':  # Если заявка ещё не завершена
                order.complete(user)  # Завершаем заявку
                return Response({'message': 'Заявка успешно завершена!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Заявка уже завершена.'}, status=status.HTTP_400_BAD_REQUEST)

        # Обрабатываем статус "отклонена"
        elif new_status == 'rejected':
            if order.status != 'rejected':  # Если заявка ещё не отклонена
                order.reject(user)  # Отклоняем заявку
                return Response({'message': 'Заявка успешно отклонена!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Заявка уже отклонена.'}, status=status.HTTP_400_BAD_REQUEST)

# DELETE удаление заявки
class OrderDeleteView(APIView):
    permission_classes = [IsAuthenticated]  # Доступ только для авторизованных пользователей

    @swagger_auto_schema(
        operation_description="Удалить заявку по ID",
        responses={
            200: openapi.Response(description="Заявка успешно удалена"),
            404: "Заявка не найдена"
        }
    )
    def delete(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')  # Получаем ID заявки из URL
        user = request.user  # Получаем текущего пользователя

        # Получаем заявку или возвращаем 404, если она не найдена
        order = get_object_or_404(Order, id=order_id)

        # Логируем удаление заявки пользователем
        print(f"User {user.username} is attempting to delete order {order_id}")

        # Обновляем или фиксируем дату завершения перед удалением, если нужно
        order.mark_as_deleted()

        # Удаляем заявку
        order.delete()

        return Response({'message': 'Order deleted successfully!'}, status=status.HTTP_200_OK)
    

class DeleteOrderParkingView(APIView):
    permission_classes = [IsAuthenticated]  # Доступ только для авторизованных пользователей

    @swagger_auto_schema(
        operation_description="Удалить позицию из заявки",
        responses={
            200: openapi.Response(description="Паркинг успешно удален из заявки"),
            404: openapi.Response(description="Паркинг не найден в этой заявке")
        }
    )
    def delete(self, request, order_id, parking_id):
        # Получаем заявку по ID
        order = get_object_or_404(Order, id=order_id)

        # Находим паркинг по ID
        parking = get_object_or_404(Parking, id=parking_id)

        # Проверяем, есть ли связь между заказом и паркингом
        related_parking = OrderParking.objects.filter(order=order, parking=parking).first()

        if not related_parking:
            logger.error(f"Parking {parking_id} not found in order {order_id}")
            return Response({'detail': 'Паркинг не найден в этой заявке'}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем связь
        related_parking.delete()
        logger.info(f"Removed parking {parking_id} from order {order_id}")

        return Response({'detail': f'Паркинг {parking_id} успешно удален из заявки {order_id}'}, status=status.HTTP_200_OK)

# PUT обновление позиции в заявке
class UpdateOrderParkingView(APIView):
    permission_classes = [IsAuthenticated]  # Доступ только для авторизованных пользователей

    @swagger_auto_schema(
        operation_description="Обновить количество паркинга в заявке",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Новое количество паркинга'),
            },
        ),
        responses={
            200: openapi.Response(description="Количество успешно обновлено"),
            400: openapi.Response(description="Некорректное количество"),
            404: openapi.Response(description="Заказ или паркинг не найдены"),
        }
    )
    def put(self, request, order_id, parking_id):
        user = request.user  # Получаем текущего пользователя

        # Попытка получить экземпляр OrderParking
        try:
            order_parking = OrderParking.objects.get(order_id=order_id, parking_id=parking_id, user=user)
        except OrderParking.DoesNotExist:
            logger.error(f"OrderParking with order_id={order_id}, parking_id={parking_id}, user_id={user.id} does not exist.")
            return Response({'detail': 'Заказ или паркинг не найдены.'}, status=status.HTTP_404_NOT_FOUND)

        # Получаем количество из данных запроса
        quantity = request.data.get('quantity')

        # Логируем полученное количество
        logger.info(f"Received quantity: {quantity}")
        
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            logger.warning(f"Invalid quantity received: {quantity}. Must be an integer.")
            return Response({'error': 'Количество должно быть положительным целым числом'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что количество положительное
        if quantity is not None:
            if isinstance(quantity, int) and quantity > 0:
                order_parking.quantity = quantity
                order_parking.save()
                logger.info(f"Updated quantity for order_parking {order_parking.id} to {quantity}")
                return Response({'status': 'Количество обновлено', 'new_quantity': order_parking.quantity}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Invalid quantity received: {quantity}")
                return Response({'error': 'Количество должно быть положительным целым числом'}, status=status.HTTP_400_BAD_REQUEST)

        logger.warning("Quantity not provided in request.")
        return Response({'error': 'Не указано количество для обновления'}, status=status.HTTP_400_BAD_REQUEST)
    



class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

import uuid

@swagger_auto_schema(method='post', request_body=LoginSerializer)

@api_view(['POST'])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]
    user = authenticate(request, email=username, password=password)
    if user is not None:
        login(request, user)
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

def logout_view(request):
    logout(request._request)
    return Response({'status': 'Success'})
