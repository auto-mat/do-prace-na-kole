docker-compose: Dockerfile Pipfile Pipfile.lock DockerfileDev
	sudo docker build -t dpnk-base .
	sudo docker-compose -f docker-compose-dev.yml build
	sudo docker-compose -f docker-compose-dev.yml down
	sudo docker-compose -f docker-compose-dev.yml up

