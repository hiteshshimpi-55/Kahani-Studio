.PHONY: run build down logs stop prod

# Hot-reload stack (FE Vite HMR + API --reload + worker watch). First boot builds images.
run:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Same as run, detached
build:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Production-like images (nginx web, no source mounts). Use after dependency changes if needed.
prod:
	docker compose up --build

# Stop and remove containers
down:
	docker compose down

stop: down

# Tail compose logs
logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
