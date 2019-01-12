#!/bin/bash
NodeName=$(docker-machine ls -q --filter label="createdBy=adaptation-manager")
echo $NodeName
COUNTER=0
for i in "${NodeName[@]}"
do
   echo "$i" "$COUNTER"
   let "COUNTER= $COUNTER + 1"
done

if [ $COUNTER -gt 0 ]
   	then
   		 
   		echo Hey that\'s a large number."$COUNTER"
   		docker-machine rm -f -y $i
   		eval $(docker-machine env nupic)
   		docker node rm $i
   		docker-machine ls 
   	fi
   # or do whatever with individual element of the array

#docker-machine rm -f -y $i