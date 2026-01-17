# Makefile for Bathhouse Booking project

.PHONY: help up down logs ps migrate test init init-dev bot-logs restart-bot

help:
	@echo "Available commands:"
	@echo "  make up       - Start containers in background"
	@echo "  make down     - Stop and remove containers"
	@echo "  make logs     - Show container logs"
	@echo "  make ps       - Show container status"
	@echo "  make migrate  - Run database migrations"
	@echo "  make test     - Run tests locally"
	@echo "  make init     - Initialize project (safe)"
	@echo "  make init-dev - Initialize project with dev superuser"
	@echo "  make bot-logs - Show bot container logs"
	@echo "  make restart-bot - Restart bot container"

# Basic commands
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

migrate:
	docker compose exec web python manage.py migrate

test:
	pytest -q

# Safe initialization
init: up
	@echo "Waiting for PostgreSQL to be healthy..."
	@timeout 60 bash -c 'until [ "$$(docker inspect -f {{.State.Health.Status}} $$(docker compose ps -q db))" = "healthy" ]; do sleep 2; done'
	@echo "Running migrations..."
	@docker compose exec web python manage.py migrate
	@echo "Initialization complete!"

# Dev-only initialization with superuser
init-dev: init
	@echo "Creating/updating dev superuser..."
	@docker compose exec web python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); user, created = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'}); user.email='admin@example.com'; user.is_staff=True; user.is_superuser=True; user.set_password('$(or $(ADMIN_PASSWORD),admin123)'); user.save(); print('DEV superuser: admin/$(or $(ADMIN_PASSWORD),admin123)')"

# Bot commands
bot-logs:
	docker compose logs -f --tail=200 bot

restart-bot:
	docker compose restart bot
