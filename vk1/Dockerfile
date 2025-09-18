# Используем Python 3.11 как базовый образ
FROM python:3.11-slim

# Установка зависимостей для Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем необходимые файлы
COPY posts.xlsx .
COPY inner.png .
COPY requirements.txt .
COPY *.py .
COPY vk_storage.json .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для хранения данных и скриншотов
RUN mkdir -p /app/assets /app/log

# Запускаем основной скрипт
CMD ["python", "main.py"]