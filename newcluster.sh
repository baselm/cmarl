#!/bin/bash
docker-machine create -d virtualbox new-mgr

eval $(docker-machine env new-mgr)

docker swarm init \
    --advertise-addr $(docker-machine ip new-mgr)

ADMIN_USER=admin ADMIN_PASSWORD=admin docker stack deploy -c basic-docker-compose.yml mon3

docker swarm join-token -q manager

TOKEN=$(docker swarm join-token -q manager)

eval $(docker-machine env nupic)
docker swarm leave --force 
 docker swarm join \
    --token $TOKEN \
    --advertise-addr $(docker-machine ip nupic) \
    $(docker-machine ip new-mgr):2377

docker node ls 