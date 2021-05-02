docker-compose: Dockerfile pyproject.toml poetry.lock DockerfileDev
	sudo docker build -t dpnk-base .
	sudo docker-compose build
	sudo docker-compose down
	sudo docker-compose up

