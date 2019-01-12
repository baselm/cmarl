#!/bin/bash
NodeName=$(docker-machine ls -q --filter label="createdBy=adaptation-manager")
echo "${NodeName[0]}"
set -- $NodeName
echo Hey that\'s a large number. ${#NodeName[@]}
docker-machine rm -f -y "$1"
eval $(docker-machine env nupic)
docker node rm "${NodeName[0]}"
docker-machine ls 
  
   # or do whatever with individual element of the array

#docker-machine rm -f -y $i