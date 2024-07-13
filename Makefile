clean:
	rm temp-*.sh
	rm log*.txt
	rm config*.txt
	rm user-image.simg
	rm example.conf
	rm stdout.txt
	rm .tox
	rm boutiques.egg-info
	rm boutiques-example1-test.simg

docker_build: boutiques/schema/examples/example1/
	docker build -t boutiques/example1:test boutiques/schema/examples/example1

boutiques-example1-test.simg: docker_build
	bash tools/docker2singularity.sh
