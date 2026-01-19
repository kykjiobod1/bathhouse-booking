# Makefile for Bathhouse Booking project

.PHONY: help up down logs ps migrate test init ensure-dirs env superuser collectstatic bot-logs restart-bot

help:
	@echo "Available commands:"
	@echo "  make env          - Create .env from .env.example if missing"
	@echo "  make ensure-dirs  - Create required directories"
	@echo "  make up           - Start containers in background with build"
	@echo "  make down         - Stop and remove containers"
	@echo "  make logs         - Show container logs"
	@echo "  make ps           - Show container status"
	@echo "  make migrate      - Run database migrations"
	@echo "  make collectstatic - Collect static files"
	@echo "  make test         - Run tests locally"
	@echo "  make init         - Initialize project: up + ensure-dirs + migrate + collectstatic"
	@echo "  make superuser    - Create admin superuser from env"
	@echo "  make bot-logs     - Show bot container logs"
	@echo "  make restart-bot  - Restart bot container"

# Environment setup
env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your actual values"; \
	else \
		echo ".env already exists, skipping..."; \
	fi

# Directory setup
ensure-dirs:
	@mkdir -p bathhouse_booking/logs bathhouse_booking/staticfiles logs

# Basic commands
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

migrate:
	@echo "Waiting for PostgreSQL to be healthy..."
	@timeout 60 bash -c 'until [ "$$(docker inspect -f {{.State.Health.Status}} $$(docker compose ps -q db))" = "healthy" ]; do sleep 2; done'
	@echo "Running migrations..."
	@docker compose exec web python manage.py migrate

collectstatic:
	@docker compose exec web python manage.py collectstatic --noinput

test:
	pytest -q

# Safe initialization
init: up ensure-dirs migrate collectstatic superuser
	@echo "Initialization complete!"

# Create superuser from environment
superuser:
	@docker compose exec web python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); user, created = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'}); user.email='admin@example.com'; user.is_staff=True; user.is_superuser=True; user.set_password('$(or $(ADMIN_PASSWORD),admin123)'); user.save(); print('Superuser created/updated: admin')"

# Bot commands
bot-logs:
	docker compose logs -f --tail=200 bot

restart-bot:
	docker compose restart bot
