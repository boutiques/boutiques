clean:
	rm -rf temp-*.sh log*.txt config*.txt user-image.simg example.conf stdout.txt

docker_build:
	docker build -t boutiques/example1:test ./boutiques/schema/examples/example1

docker2singularity:
	bash tools/docker2singularity.sh
