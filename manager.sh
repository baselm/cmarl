#!/bin/bash
export VIRTUALBOX_BOOT2DOCKER_URL=/Users/baz/.docker/machine/cache/boot2docker.iso
RIGHT_NOW=$(date +"%F"-"%h%M%S")
echo $RIGHT_NOW
docker-machine create -d virtualbox \
--engine-label createdBy=adaptation-manager \
--engine-label role=manager \
mgr-$RIGHT_NOW
eval $(docker-machine env nupic)

TOKEN=$(docker swarm join-token -q manager)

eval $(docker-machine env mgr-$RIGHT_NOW)

docker swarm join --advertise-addr $(docker-machine ip mgr-$RIGHT_NOW) \
        --token $TOKEN $(docker-machine ip nupic):2377
eval $(docker-machine env nupic)
docker node ls