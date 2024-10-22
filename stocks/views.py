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
from rest_framework import filters
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
    ordering_fields = ['name', 'open_hour']  # Поля для сортировки

    def get_queryset(self):
        # Получаем черновик заявки пользователя, если она существует
        draft_order = Order.objects.filter(user=self.request.user, status='draft').first()

        # Начинаем с базового queryset
        queryset = Parking.objects.all()

        # Получаем параметры фильтрации из запроса
        name = self.request.query_params.get('name')
        place = self.request.query_params.get('place')
        sports = self.request.query_params.get('sports')
        open_hour = self.request.query_params.get('open_hour')
        close_hour = self.request.query_params.get('close_hour')
        status = self.request.query_params.get('status')

        # Фильтруем по имени, если указано
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Фильтруем по месту, если указано
        if place:
            queryset = queryset.filter(place__icontains=place)

        # Фильтруем по виду спорта, если указано
        if sports:
            queryset = queryset.filter(sports__icontains=sports)

        # Фильтруем по времени открытия, если указано
        if open_hour:
            queryset = queryset.filter(open_hour__gte=open_hour)

        # Фильтруем по времени закрытия, если указано
        if close_hour:
            queryset = queryset.filter(close_hour__lte=close_hour)

        # Фильтруем по статусу, если указано
        if status is not None:  # Проверка на None для BooleanField
            queryset = queryset.filter(status=status)

        # Если черновик заявки существует, аннотируем количество услуг
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
        if draft_order:
            response.data = {
                'draft_order_id': draft_order.id,
                'services_in_draft_order': services_in_draft_order,  # Динамическое количество услуг
                'parkings': response.data  # Список парковок
            }
        else:
            response.data = {
                'draft_order_id': None,
                'services_in_draft_order': 0,
                'parkings': response.data
            }

        return Response(response.data)

# GET одна запись услуги
class ParkingDetailView(generics.RetrieveAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

# POST добавление услуги
class ParkingCreateView(generics.CreateAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

# PUT изменение услуги
class ParkingUpdateView(generics.UpdateAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

# DELETE удаление услуги
class ParkingDeleteView(generics.DestroyAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

    def delete(self, request, *args, **kwargs):
        parking = self.get_object()
        parking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AddParkingToDraftOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Get the parking instance by ID
        try:
            parking = Parking.objects.get(pk=pk)
        except Parking.DoesNotExist:
            return Response({"detail": "Parking not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get or create the order for the authenticated user
        order, created = Order.objects.get_or_create(
            user=request.user,
            status='draft',  # Assuming 'draft' is the status for new orders
            defaults={'created_at': timezone.now()}
        )

        # Check if the parking already exists in the order
        order_parking, order_parking_created = OrderParking.objects.get_or_create(
            order=order,
            parking=parking,
            user=request.user,
            defaults={'quantity': 1}  # Set initial quantity to 1 if new
        )

        if not order_parking_created:
            # If the parking item already exists, increment the quantity
            order_parking.quantity += 1
            order_parking.save()  # Save the updated quantity

        return Response({
            "detail": "Parking added to draft order.",
            "quantity": order_parking.quantity
        }, status=status.HTTP_201_CREATED)
        
# POST добавление изображения для услуги
class AddImageToParkingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # 1. Получаем объект паркинга по ID
        parking = get_object_or_404(Parking, pk=pk)

        # 2. Получаем загруженное изображение из запроса
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            return Response({"detail": "No image uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Удаляем старое изображение, если оно существует
        if parking.image_card:
            try:
                minio_client.remove_object(settings.MINIO_STORAGE_MEDIA_BUCKET_NAME, parking.image_card)
                logger.info(f"Deleted old image: {parking.image_card}")
            except S3Error as e:
                logger.error(f"Error deleting old image: {e}")
                return Response({"detail": f"Error deleting old image: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Загружаем новое изображение в MinIO
        file_name = f"parkings/{parking.id}/{timezone.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        try:
            minio_client.put_object(
                settings.MINIO_STORAGE_MEDIA_BUCKET_NAME,
                file_name,
                uploaded_file.file,
                uploaded_file.size,
                content_type=uploaded_file.content_type  # Указываем MIME тип файла
            )
            logger.info(f"Uploaded new image: {file_name}")
        except S3Error as e:
            logger.error(f"Error uploading image: {e}")
            return Response({"detail": f"Error uploading image: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5. Обновляем запись паркинга с новым путем к изображению
        parking.image_card = file_name
        parking.save()

        # 6. Возвращаем URL загруженного изображения
        return Response({
            "detail": "Image uploaded successfully.", 
            "image_url": minio_client.presigned_get_object(settings.MINIO_STORAGE_MEDIA_BUCKET_NAME, file_name)
        }, status=status.HTTP_200_OK)



# GET список заявок с фильтрацией
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.exclude(status='deleted').exclude(status='draft')  # Не показывать удаленные и черновики
        
        # Получение параметров фильтрации
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        status = self.request.query_params.get('status', None)

        # Фильтрация по дате
        if start_date:
            queryset = queryset.filter(created_at__gte=datetime.fromisoformat(start_date))
        if end_date:
            queryset = queryset.filter(created_at__lte=datetime.fromisoformat(end_date))
        if status:
            queryset = queryset.filter(status=status)

        return queryset

# GET одна заявка
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    queryset = Order.objects.all()

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

# PUT сформировать заявку (создателем)
class OrderFormedView(APIView):

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
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи

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
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи

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
    

# DELETE удаление позиции из заявки
class DeleteOrderParkingView(APIView):

    def delete(self, request, order_id, parking_id):
        # Получаем заявку по ID
        order = get_object_or_404(Order, id=order_id)

        # Находим паркинг по ID
        parking = get_object_or_404(Parking, id=parking_id)

        # Проверяем, есть ли связь между заказом и паркингом
        related_parking = OrderParking.objects.filter(order=order, parking=parking).first()

        if not related_parking:
            return Response({'detail': 'Parking not found in this order'}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем связь
        related_parking.delete()

        return Response({'detail': f'Parking {parking_id} removed from order {order_id}'}, status=status.HTTP_200_OK)

class UpdateOrderParkingView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id, parking_id):
        user = request.user  # Get the current user

        # Attempt to retrieve the OrderParking instance
        try:
            order_parking = OrderParking.objects.get(order_id=order_id, parking_id=parking_id, user=user)
        except OrderParking.DoesNotExist:
            logger.error(f"OrderParking with order_id={order_id}, parking_id={parking_id}, user_id={user.id} does not exist.")
            return Response({'detail': 'No OrderParking matches the given query.'}, status=status.HTTP_404_NOT_FOUND)

        # Get the quantity from the request data
        quantity = request.data.get('quantity')

        # Log the received quantity
        logger.info(f"Received quantity: {quantity}")
        
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            logger.warning(f"Invalid quantity received: {quantity}. Must be an integer.")
            return Response({'error': 'Количество должно быть положительным целым числом'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the quantity is a positive integer
        if quantity is not None:
            if isinstance(quantity, int) and quantity > 0:
                order_parking.quantity = quantity
                order_parking.save()
                return Response({'status': 'Количество обновлено', 'new_quantity': order_parking.quantity}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Invalid quantity received: {quantity}")
                return Response({'error': 'Количество должно быть положительным целым числом'}, status=status.HTTP_400_BAD_REQUEST)

        logger.warning("Quantity not provided in request.")
        return Response({'error': 'Не указано количество для обновления'}, status=status.HTTP_400_BAD_REQUEST)
    
# POST регистрация пользователя
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи

    def get_object(self):
        # Возвращает текущего пользователя
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()  # Получаем текущего пользователя
        serializer = self.get_serializer(user, data=request.data, partial=True)  # Позволяет частичное обновление

        if serializer.is_valid():
            serializer.save()  # Сохраняем обновленные данные пользователя
            return Response(serializer.data, status=status.HTTP_200_OK)  # Возвращаем обновленные данные
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Возвращаем ошибки валидации
    
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]  # Разрешаем доступ неавторизованным пользователям

    def post(self, request, *args, **kwargs):
        # Получаем данные из запроса
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():

            # Аутентификация пользователя
            
            return Response({'message': 'User authenticated successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
    

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи

    def post(self, request, *args, **kwargs):
        return Response({'message': 'User logged out successfully'}, status=status.HTTP_200_OK)