# Система аналитики с Kafka и Redis

Этот проект демонстрирует реализацию отслеживания движения мыши с ограничением частоты событий (троттлингом), отправкой данных на сервер, и сохранением данных в Kafka, Redis и PostgreSQL.

## Функциональность

- Отслеживание движения мыши с ограничением до одного события каждые 250 мс
- Получение координат курсора (clientX, clientY)
- Отправка координат в формате JSON на серверный endpoint
- Использование уникального идентификатора пользователя
- Публикация данных в топик Kafka
- Сохранение последней позиции мыши в Redis
- Сохранение аналитических данных в PostgreSQL
- Возможность включения и отключения отслеживания
- Визуализация данных в Grafana

## Архитектура

Система состоит из следующих компонентов:
- **Веб-интерфейс** - отслеживает движения мыши и отправляет координаты 
- **API** - принимает координаты и публикует их в Kafka
- **Kafka** - брокер сообщений для обработки событий
- **Redis** - хранит последнюю позицию мыши для быстрого доступа
- **Kafka-to-Redis** - консьюмер, сохраняющий данные из Kafka в Redis
- **PostgreSQL** - сохраняет данные для долгосрочного анализа
- **Kafka-to-PostgreSQL** - консьюмер, сохраняющий данные из Kafka в PostgreSQL
- **Grafana** - платформа для визуализации данных из Redis и PostgreSQL

## Структура проекта

- `app.py` - основное Flask-приложение с API-эндпоинтами
- `static/js/main.js`, `static/js/mouseTracker.js`, `static/js/direct-mouse-tracker.js` - JavaScript модули для frontend
- `kafka_integration.py` - модуль для интеграции с Kafka
- `kafka_to_redis_consumer.py` - консьюмер для сохранения данных в Redis
- `kafka_to_postgres.py` - консьюмер для сохранения данных в PostgreSQL
- `templates/` - HTML-шаблоны для веб-интерфейса
- `static/` - статические файлы CSS и JavaScript
- `docker-compose.yml` - файл для запуска всех компонентов в Docker

## Установка и запуск

### Запуск с помощью Docker Compose

1. Установите Docker и Docker Compose
2. Запустите все контейнеры:
```
docker-compose up -d
```

### Тестирование

После запуска системы с помощью Docker Compose (локально или через CI/CD):

1. Откройте веб-интерфейс по адресу: **http://kafka-test.info/** (при развертывании на сервере) или http://localhost:80 (при локальном запуске, если порт 80 свободен).
2. Нажмите кнопку "Запустить отслеживание" или "Запустить прямое отслеживание".
3. Проверьте, что координаты мыши успешно отправляются в API (статус должен обновляться на странице).

## Доступ к Grafana

Для визуализации данных:

1. Откройте Grafana по адресу http://localhost:3001
2. Используйте логин/пароль: admin/admin
3. При первом входе вам будет предложено сменить пароль

### Настройка дашборда в Grafana

Графические панели для отображения координат мыши:

1. Создайте новый дашборд
2. Добавьте панель для визуализации координат мыши:
   - **XY Chart** - для отображения X и Y координат на двухмерном графике
   - **Time Series** - для отображения изменения координат во времени
   - **Table** - для отображения детальной информации о событиях

3. Настройка источника данных Redis:
   - Откройте "Настройки" → "Data Sources" → "Add data source"
   - Выберите "Redis"
   - Настройте подключение: хост - `redis`, порт - `6379`
   
4. Настройка источника данных PostgreSQL:
   - Откройте "Настройки" → "Data Sources" → "Add data source"
   - Выберите "PostgreSQL"
   - Настройте подключение: хост - `localhost`. порт - `5432`, база данных - `mousetracker`, пользователь - `postgres`, пароль - `postgres`

## Интеграция в свой проект

```javascript
import { initMouseTracker, stopMouseTracker } from './mouseTracker.js';

// Запуск отслеживания
initMouseTracker();

// Остановка отслеживания
stopMouseTracker();
```

## Настройка серверного endpoint

По умолчанию данные отправляются на `/api/coordinates`. Для изменения endpoint отредактируйте соответствующий URL в функции `sendCoordinates` файла `mouseTracker.js`.

## Примечание

Демонстрационная версия перехватывает запросы fetch для визуализации данных без реального сервера.
В продакшн-версии обязательно настройте соответствующий обработчик на серверной стороне.

Удалены тестовые, временные файлы и скрипты:
- latest_analytics.txt
- user_data_count.txt
- count.txt
- postgres_query_result.txt
- redis_consumer.log
- redis_tools.py
- kafka_consumer_for_coordinates.py
- redis-only.yml

## Диагностика и отладка

В случае возникновения проблем с системой:

### Проверка состояния контейнеров

```bash
docker-compose ps
```

### Просмотр логов

Для просмотра логов конкретного сервиса:

```bash
docker-compose logs -f [имя_сервиса]
```

Доступные сервисы:
- api
- kafka1
- kafka2
- redis
- zookeeper
- postgres
- kafka-to-redis
- kafka-to-postgres
- grafana
- nginx

### Проверка соединения с Kafka

```bash
docker-compose exec kafka1 kafka-topics --list --bootstrap-server kafka1:9092
```

### Просмотр данных в PostgreSQL

```bash
docker-compose exec postgres psql -U postgres -d mousetracker -c "SELECT * FROM mouse_coordinates LIMIT 10;"
```

### Проверка данных в Redis

```bash
docker-compose exec redis redis-cli KEYS "*"
```
