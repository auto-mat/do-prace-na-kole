docker-compose: Dockerfile Pipfile Pipfile.lock DockerfileDev
	sudo docker build -t dpnk-base .
	sudo docker-compose build
	sudo docker-compose down
	sudo docker-compose up

