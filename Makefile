docker_build:
	docker build -t boutiques/example1:test ./boutiques/schema/examples/example1

docker2singularity:
	bash tools/docker2singularity.sh
