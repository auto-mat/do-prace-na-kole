docker-compose: Dockerfile DockerfileDev
	mkdir -p pyenv
	mkdir -p db
	sudo docker build -t dpnk-base .
	sudo docker-compose build
	sudo docker-compose down
	sudo docker-compose up

