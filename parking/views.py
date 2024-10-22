from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.db import connection  # Импортируем для использования SQL
from .models import Parking, Order, OrderParking
from django.utils.dateformat import DateFormat
from .data import CARDS_DATA
from django.contrib.auth.decorators import login_required

def Parking_BMSTU(request):
    hour = request.GET.get('text', '')  # Время работы, введенное пользователем
    cards = Parking.objects.all()  # Все парковки
    if hour.isdigit():
        hour = int(hour)
        cards = cards.filter(open_hour__lte=hour, close_hour__gte=hour)

    # Получаем черновой заказ для текущего пользователя
    draft_order = Order.objects.filter(user=request.user, status='draft').first()  # Получаем первый черновой заказ для текущего пользователя

    context = {
        'cards': cards,
        'draft_order': draft_order
    }
    return render(request, 'main.html', context)

def ParkingSearch(request):
    if request.method == 'POST':
        hour = request.POST.get('text', '')  # Получаем введённый текст из формы
        cards = Parking.objects.all()  # Все парковки

        if hour.isdigit():
            hour = int(hour)
            cards = cards.filter(open_hour__lte=hour, close_hour__gte=hour)

        # Получаем черновой заказ для текущего пользователя
        draft_order = Order.objects.filter(user=request.user, status='draft').first()

        context = {
            'cards': cards,
            'draft_order': draft_order
        }

        return render(request, 'main.html', context)

    # Если не POST-запрос, перенаправляем на главную
    return redirect('Parking_BMSTU')

def information(request, id):
    parking = get_object_or_404(Parking, id=id)
    
    # Поиск соответствующей записи в data.py
    card_data = next((item for item in CARDS_DATA if item['id'] == parking.id), None)
    
    # Получаем изображение из data.py
    image_url = card_data['image'] if card_data else None

    # Передаем данные в шаблон
    context = {
        'parking': parking,
        'image_url': image_url
    }

    return render(request, 'second.html', context)


def Pass(request, id):
    # Получаем текущий черновой заказ для пользователя
    draft_order = Order.objects.filter(id=id, status='draft', user=request.user).first()

    # Если заказ существует, передаем данные в шаблон
    context = {
        'draft_order': draft_order,
        'user_name': request.user.get_full_name()  # Получаем ФИО пользователя
    }

    if draft_order:
        # Если черновой заказ существует, добавляем информацию о сроке действия абонемента и гос. номере
        if draft_order.state_number:  # Проверка на наличие гос. номера
            context['state_number'] = draft_order.state_number  # Гос номер ТС
        if draft_order.planned_deadline:  # Проверка на наличие срока действия
            context['planned_deadline'] = DateFormat(draft_order.planned_deadline).format('d.m.Y')    
    
    return render(request, 'third.html', context)

def clear_Pass(request):
    # Получаем текущий черновой заказ для текущего пользователя
    draft_order = Order.objects.filter(user=request.user, status='draft').first()
    
    if draft_order:
        # Устанавливаем статус заказа на "удален" с помощью SQL-запроса
        with connection.cursor() as cursor:
            cursor.execute("UPDATE orders SET status = 'deleted' WHERE id = %s", [draft_order.id])

    # Редирект на главную страницу
    return redirect('Parking_BMSTU')


def add_to_Pass(request, parking_id):
    if request.method == 'POST':
        parking = get_object_or_404(Parking, id=parking_id)
        quantity = int(request.POST.get('quantity', 0))

        if quantity > 0:
            # Получаем или создаём черновик заказа для текущего пользователя
            order, created = Order.objects.get_or_create(user=request.user, status='draft')

            # Пытаемся получить существующий элемент заказа
            order_parking, created = OrderParking.objects.get_or_create(
                order=order,
                parking=parking,
                user=request.user
            )

            # Увеличиваем количество
            order_parking.quantity += quantity  # Обновляем quantity
            order_parking.save()  # Сохраняем элемент заказа

        return redirect('Parking_BMSTU')  # Перенаправляем на главную страницу
    return redirect('Parking_BMSTU')  # В случае не POST перенаправляем на главную


def create_draft_order(id):
    """Создание тестового чернового заказа."""
    order = {
        "id": id,
        "planned_date": '25.09.2024',
        "parts": []
    }
    parking = Parking.objects.filter(id=id).first()
    if parking:
        order["parts"].append({
            'id': parking.id,
            'image': parking.image_card,
            'name': parking.name,
            'quantity': 1,
        })
    return order
