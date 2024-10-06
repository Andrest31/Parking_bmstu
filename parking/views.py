# views.py
from django.shortcuts import render
from data import CARDS_DATA
from draft_order import create_draft_order


def hello(request):
    hour = request.GET.get('text', '')  # Получаем введенное пользователем число
    cards = CARDS_DATA  # Все карточки
    DRAFT_ORDER = create_draft_order(123)

    # Если введено число и оно валидно, фильтруем карточки
    if hour.isdigit():
        hour = int(hour)
        cards = [card for card in CARDS_DATA if card['open_hour'] <= hour <= card['close_hour']]
        
    context = {
        'cards': cards,
        'draft_order': DRAFT_ORDER
    }
    return render(request, 'main.html', context)

def information(request, id):
    # Find the parking by ID
    parking = next((item for item in CARDS_DATA if item['id'] == id), None)
    
    if parking is None:
        return render(request, '404.html', status=404)
    
    return render(request, 'second.html', {'parking': parking})

def cart(request, id):
    # Here, we will define a draft order based on the id passed in the URL
    DRAFT_ORDER = create_draft_order(id)
    
    context = {
        'draft_order': DRAFT_ORDER
    }
    
    return render(request, 'third.html', context)
