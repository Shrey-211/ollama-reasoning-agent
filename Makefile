.PHONY: docker-build docker-up docker-down test run
docker-build:
	docker build -t ollama-reasoning-agent .
docker-up:
	docker-compose up --build -d
docker-down:
	docker-compose down
test:
	pytest -q
run:
	python src/main.py
