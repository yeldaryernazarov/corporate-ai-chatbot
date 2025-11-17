# Используем официальный Python образ
FROM python:3.10-slim

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Установить рабочую директорию
WORKDIR /app

# Копировать requirements.txt
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копировать исходный код
COPY . .

# Создать директории для данных
RUN mkdir -p /app/data/finance /app/data/legal /app/data/project

# Открыть порт для мониторинга (опционально)
EXPOSE 9090

# Установить переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Команда запуска
CMD ["python", "src/main.py"]
