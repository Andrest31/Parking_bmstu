from django.db import models
from django.contrib.auth.models import User

# Модель Заказ (Order)
class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Добавлено поле user
    planned_date = models.DateTimeField(null=True, blank=True)
    planned_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    sumbited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    state_number = models.CharField(max_length=10, null=True, blank=True)
    status_choices = [
        ('draft', 'Черновик'),
        ('deleted', 'Удален'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершен'),
        ('rejected', 'Отклонен'),
    ]
    status = models.CharField(max_length=9, choices=status_choices)

    class Meta:
        db_table = 'orders'


# Модель Позиции в заказе (OrderItem)
class OrderParking(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, models.DO_NOTHING, related_name='parkings')
    parking = models.ForeignKey('Parking', models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Добавлено поле user
    quantity = models.IntegerField(default=0)  # Установка значения по умолчанию

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
