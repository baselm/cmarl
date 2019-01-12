#!/bin/bash
eval $(docker-machine env nupic)
docker rm $(docker ps -qa --no-trunc --filter "status=exited")
docker ps