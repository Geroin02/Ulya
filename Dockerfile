FROM python:3.10-slim

WORKDIR /app

# 1. Ставим системные пакеты до установки Python-зависимостей
RUN apt-get update && apt-get install -y git ffmpeg && rm -rf /var/lib/apt/lists/*

# 2. Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Копируем код
COPY . .

# 4. Запуск бота
CMD ["python", "main.py"]
