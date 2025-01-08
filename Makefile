run:
	@nohup python3 main.py </dev/null >/dev/null 2>&1 &
check:
	@ps aux | grep "main.py"
health:
	@nohup python3 health.py </dev/null  > /dev/null 2>&1 &
all:
	@nohup python3 main.py </dev/null >/dev/null 2>&1 &
	@nohup python3 health.py </dev/null  > /dev/null 2>&1 &
