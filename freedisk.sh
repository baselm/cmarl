#!/bin/bash

 
eval $(docker-machine env nupic)
docker rmi $(docker images --filter "dangling=true" -q --no-trunc)
docker images | grep "none"
docker rmi $(docker images | grep "none" | awk '/ / { print $3 }')
docker volume prune -f
docker images