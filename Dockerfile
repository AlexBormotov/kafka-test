FROM python:3.9-slim

WORKDIR /app

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем структуру директорий для статических файлов
RUN mkdir -p /app/static/js

# Копируем статические файлы отдельно (чтобы улучшить кэширование при сборке)
COPY static/ /app/static/

# Копируем шаблоны отдельно
COPY templates/ /app/templates/

# Копируем исходный код
COPY *.py /app/

# По умолчанию запускаем компонент для обработки Kafka -> PostgreSQL
CMD ["python", "kafka_to_postgres.py"] 