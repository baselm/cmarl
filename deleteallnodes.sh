#!/bin/bash
NodeName=$(docker-machine ls -q --filter label="createdBy=adaptation-manager")
for i in $NodeName; do
  docker-machine rm -f $i
done

