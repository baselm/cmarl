export VIRTUALBOX_BOOT2DOCKER_URL=/Users/baz/.docker/machine/cache/boot2docker.iso

for i in 1 2 3 4 5; do
    docker-machine create -d virtualbox node-$i
done

eval $(docker-machine env nupic)

 
docker swarm join-token -q worker

TOKEN=$(docker swarm join-token -q worker)

for i in 1 2 3 4 5; do
  eval $(docker-machine env node-$i)

  docker swarm join \
    --token $TOKEN \
    --advertise-addr $(docker-machine ip node-$i) \
    $(docker-machine ip nupic):2377
done

eval $(docker-machine env nupic)

docker node ls