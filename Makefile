.PHONY: run check stop docker-up docker-down docker-logs

# ---------- Classic (uv, no Docker) ----------
run:
	@mkdir -p logs
	@PYTHONPATH="." nohup uv run src/app.py > logs/app.log 2>&1 &
	@echo "Bot started in background. Logs written to logs/app.log"

check:
	@ps aux | grep -E "src/app\.py" | grep -v grep

stop:
	@pkill -f "src/app.py" || true
	@echo "Bot stopped."

# ---------- Docker ----------
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f --tail=100
