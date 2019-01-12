#!/bin/bash

RIGHT_NOW=$(date +"%F"-"%h%M%S")
echo $RIGHT_NOW
docker-machine create -d virtualbox \
--engine-label createdBy=adaptation-manager \
--engine-label role=worker \
node-$RIGHT_NOW
eval $(docker-machine env nupic)

TOKEN=$(docker swarm join-token -q worker)

eval $(docker-machine env node-$RIGHT_NOW)

docker swarm join --advertise-addr $(docker-machine ip node-$RIGHT_NOW) \
        --token $TOKEN $(docker-machine ip nupic):2377
eval $(docker-machine env nupic)
docker node ls
