FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    locales \
    && rm -rf /var/lib/apt/lists/*
    
# Генерация русской локали
RUN sed -i '/ru_RU.UTF-8/s/^# //' /etc/locale.gen && locale-gen

# Установка русской локали по умолчанию
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

WORKDIR /app/bathhouse_booking

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
