# Используем Python 3.13 как базовый образ
FROM python:3.13-slim

# Установка необходимых зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libxcb1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxshmfence1 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры для Playwright
RUN PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers playwright install chromium firefox webkit

# Установка зависимостей для запуска браузера
RUN playwright install-deps

# Копируем все файлы проекта
COPY . .

# Создаем директорию для хранения данных и скриншотов
RUN mkdir -p /app/assets /app/log

# Запускаем основной скрипт
CMD ["python", "main.py"]