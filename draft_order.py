from data import CARDS_DATA

# Функция для генерации чернового заказа с данными из CARDS_DATA
def generate_draft_order(order):
    for part in order['parts']:
        # Find the corresponding parking by ID
        card_data = next((card for card in CARDS_DATA if card['id'] == part['id']), None)
        if card_data:
            # Replace image and name with the fetched data
            part['image'] = card_data['image_card']
            part['name'] = card_data['name']
    return order

def create_draft_order(id):
    card_data = next((card for card in CARDS_DATA if card['id'] == id), None)  
# Черновик заказа
    DRAFT_ORDER = {
        "id": id,
        "planned_date": '25.09.2024',
        "parts": [
            {
                'id': 1,  # Этот ID будет использован для поиска данных в CARDS_DATA
                'image': '',  # Эти поля будут заменены
                'name': '',
                'quantity': 1,
            },
        ]
    }
    print(DRAFT_ORDER)

    return generate_draft_order(DRAFT_ORDER)
