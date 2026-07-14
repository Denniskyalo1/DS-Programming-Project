build:
	docker build -t server_image ./server
	docker build -t lb_image ./loadbalancer

run:
	docker compose up -d

stop:
	docker compose down

clean:
	docker rm -f $$(docker ps -aq) || true

benchmark:
	cd analysis && . .venv/bin/activate && python benchmark.py

scale:
	cd analysis && . .venv/bin/activate && python scale_test.py