import requests
import json
import time

# URL API-эндпоинта
API_URL = "http://localhost:5000/api/send-data"

# Данные для отправки (как если бы пользователь нажал кнопку на сайте)
data = {
    "event_type": "button_click",
    "button_id": "send_data",
    "page": "index",
    "custom_data": {
        "test": "button_click_simulation",
        "timestamp": int(time.time())
    }
}

def test_button_click():
    """Симулирует нажатие кнопки на веб-странице отправкой POST-запроса."""
    print(f"Отправка данных о нажатии кнопки: {json.dumps(data, indent=2)}")
    
    try:
        # Отправляем данные через POST-запрос
        response = requests.post(
            API_URL,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        # Проверяем успешность запроса
        if response.status_code == 200:
            print("Успешно! Ответ сервера:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Ошибка: Код ответа {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    test_button_click()
    
    # Ждем немного, чтобы дать время на обработку сообщения
    print("Ожидаем обработку сообщения...")
    time.sleep(2)
    
    # Здесь можно добавить код для проверки, что данные попали в базу
    print("Тестирование завершено. Проверьте логи kafka_listener.py и таблицу analytics в PostgreSQL.") 