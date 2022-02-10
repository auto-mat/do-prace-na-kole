docker-compose: Dockerfile DockerfileDev
	mkdir -p pyenv
	mkdir -p db
	sudo docker build -t dpnk-base .
	sudo docker-compose build --build-arg UID=$(shell id -u)
	sudo docker-compose down
	sudo docker-compose up

