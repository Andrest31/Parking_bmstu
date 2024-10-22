from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

# Модель Заказ (Order)
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

# Модель Заказ (Order)
class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Пользователь, создавший заявку
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_orders')
    planned_date = models.DateTimeField(null=True, blank=True)
    planned_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    sumbited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)  # ФИО клиента
    license_plate = models.CharField(max_length=15, null=True, blank=True)  # Гос. номер
    total_quantity = models.IntegerField(default=0)  # Добавлено поле для общего количества мест
    status_choices = [
        ('draft', 'Черновик'),
        ('deleted', 'Удален'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершен'),
        ('rejected', 'Отклонен'),
    ]
    status = models.CharField(max_length=9, choices=status_choices)

    completed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'

    def complete(self, user):
        logger.info(f"Completing order {self.id} by moderator {user.username}")
        self.status = 'completed'
        self.moderator = user
        self.completed_at = timezone.now()
        self.save()
        logger.info(f"Order {self.id} completed with status {self.status}")

    def reject(self, user):
        logger.info(f"Rejecting order {self.id} by moderator {user.username}")
        self.status = 'rejected'
        self.moderator = user
        self.rejected_at = timezone.now()
        self.save()
        logger.info(f"Order {self.id} rejected with status {self.status}")

    def mark_as_deleted(self):
        """Обновляем нужные данные перед удалением заявки."""
        self.completed_at = timezone.now()  # Например, фиксируем дату удаления (если нужно)
        self.save()

    def delete(self, *args, **kwargs):
        """Переопределение метода удаления для предварительной обработки."""
        self.mark_as_deleted()
        super().delete(*args, **kwargs)


# Модель Позиции в заказе (OrderItem)
class OrderParking(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, models.DO_NOTHING, related_name='parkings')
    parking = models.ForeignKey('Parking', models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Добавлено поле user
    quantity = models.IntegerField(default=1)  # Установка значения по умолчанию

    class Meta:
        db_table = 'order_items'
        unique_together = (('order', 'parking', 'user'),)


# Модель Паркинг (Parking)
class Parking(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=25, null=True, blank=True)
    sports = models.CharField(max_length=100, null=True, blank=True)
    open_hour = models.IntegerField(null=True, blank=True)  # Изменено на IntegerField
    close_hour = models.IntegerField(null=True, blank=True)    
    image_card = models.CharField(max_length=200, null=True, blank=True)    
    status_choices = [
    (True, 'Действует'),
    (False, 'Закрыт'),
    ]
    status = models.BooleanField(choices=status_choices, null=True, blank=True)


    class Meta:
        db_table = 'parkings'