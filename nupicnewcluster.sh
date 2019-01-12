#!/bin/bash
export VIRTUALBOX_BOOT2DOCKER_URL=/Users/baz/.docker/machine/cache/boot2docker.iso

docker-machine create \
  --driver generic \
  --generic-ip-address=192.168.99.100 \
  --generic-ssh-key ~/.ssh/id_rsa \
  --generic-ssh-user nupic \
  nupic

eval $(docker-machine env nupic)
docker swarm leave --force 
docker swarm init \
    --advertise-addr $(docker-machine ip nupic) \
    --force-new-cluster

ADMIN_USER=admin ADMIN_PASSWORD=admin docker stack deploy -c basic-docker-compose.yml mon
NodeName=$(docker-machine ls -q --filter label="createdBy=adaptation-manager")
for i in $NodeName; do
  eval $(docker-machine env $i)
  docker swarm leave --force 
  docker swarm join \
    --token $TOKEN \
    --advertise-addr $(docker-machine ip $i) \
    $(docker-machine ip nupic):2377
done

eval $(docker-machine env nupic)

docker node ls

