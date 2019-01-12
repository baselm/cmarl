
# Adaptation Manager

Swarmprom is a starter kit for Docker Swarm monitoring with [Prometheus](https://prometheus.io/), 
[Grafana](http://grafana.org/), 
[cAdvisor](https://github.com/google/cadvisor), 
[Node Exporter](https://github.com/prometheus/node_exporter), 
[NUPICAPI](https://github.com/baselm/nupic-api.git), 
[NUPIC](https://github.com/numenta/nupic),
[Alert Manager](https://github.com/prometheus/alertmanager)
and [Unsee](https://github.com/cloudflare/unsee).

## Install

* Clone this repository and run the monitoring and adaptation stack:

```bash
$ git clone https://github.com/baselm/ieee-demo.git
$ cd ieee-demo
ADMIN_USER=admin \
ADMIN_PASSWORD=admin \
docker stack deploy -c basic-docker-compose.yml mon3
```
* This repo assumes you have all the prerequisities installed and it should work out of the box by running DQN_aftersubmission.ipynb or DQN_aftersubmission.py. The foo_agent could be installed in your system using pip install -e . 
The DQN agent create a leader node called nupic with ip address 192.168.99.100. Feel free to change the IP Address to suits you need. To use diffreant name for the leader you need to change it in the attached shell scripts. 
The agent need to be run in the docker machine host, as it needs direct access to docker engine. For more information read [docker machine documentation](https://docs.docker.com/machine/)
## Run 
```bash
python DQN_aftersubmission.py
```
The DQN_aftersubmission.ipynb contains the MDP Agent and the DQN algorithm. Running this notebook will enable the DQN to initiat the swarm and load all the services below. The agent will be able to create/remove nodes based on the current state. 

Prerequisites:

* Docker CE 17.09.0-ce or Docker EE 17.06.2-ee-3
* Swarm cluster with one manager and a worker node
* Docker engine experimental enabled and metrics address set to `0.0.0.0:9323`
* [Tensorflow](https://www.tensorflow.org)
* [Keras](https://keras.io)
* [Keras-rl](https://github.com/keras-rl/keras-rl)
* [OpenAI](https://github.com/openai/gym)

Services:

* prometheus (metrics database) `http://<swarm-ip>:9090`
* grafana (visualize metrics) `http://<swarm-ip>:3000`
* node-exporter (host metrics collector)
* cadvisor (containers metrics collector)
* dockerd-exporter (Docker daemon metrics collector, requires Docker experimental metrics-addr to be enabled)
* alertmanager (alerts dispatcher) `http://<swarm-ip>:9093`
* unsee (alert manager dashboard) `http://<swarm-ip>:9094`
* caddy (reverse proxy and basic auth provider for prometheus, alertmanager and unsee)
* NUPIC API for collecting Observation 'http://<swarm-ip>:8888'
* Swamr API could be used to train NUPIC Anomaly Detection service, but it is not included in this service stack. The following could be used to start the traning in the leader node. 
 ```bash
 docker run \
  --name nupic-mysql \
  -e MYSQL_ROOT_PASSWORD=nupic \
  -p 3306:3306 \
  -d \
  mysql:5.6

docker run \
  --name nupic \
  -e NTA_CONF_PROP_nupic_cluster_database_passwd=nupic \
  -e NTA_CONF_PROP_nupic_cluster_database_host=mysql \
  --link nupic-mysql:mysql \
  -ti \
-v mon3_docker:/model-trainer  \
-d --restart=unless-stopped \
  baselm/swarm:787
```
* MDP Agent Implemented in Openai gym
* It is recommanded to run a demo web service to be used for vertical scaling. Something similar to the following:
```bash
docker service create --replicas 1 \
--label=com.docker.swarm.service.max=20 \
--label=com.docker.swarm.service.min=1 \
--label=com.docker.swarm.service.desired=2 \
-p 80:80 --name web nginx
```

## Setup Grafana

Navigate to `http://<swarm-ip>:3000` and login with user ***admin*** password ***admin***. 
You can change the credentials in the compose file or 
by supplying the `ADMIN_USER` and `ADMIN_PASSWORD` environment variables at stack deploy.

Swarmprom Grafana is preconfigured with two dashboards and Prometheus as the default data source:

* Name: Prometheus
* Type: Prometheus
* Url: http://prometheus:9090
* Access: proxy

After you login, click on the home drop down, in the left upper corner and you'll see the dashboards there.

***Docker Swarm Nodes Dashboard***
This live [snapshot](https://snapshot.raintank.io/dashboard/snapshot/SyKQ96o2JWfuVyc43hcGgAI9YLcjk3mW?orgId=2) provides a full virtualisation of all services running in the cluster.  
A full visualised and analysis dashboard of the swarm after the adaptation can be found in this [snapshot](https://snapshot.raintank.io/dashboard/snapshot/sstuT2tuYkob8zjIbh1YXzBYxSJDFd9z?orgId=2)

URL: `http://<swarm-ip>:3000/dashboard/db/docker-swarm-nodes`

This dashboard shows key metrics for monitoring the resource usage of your Swarm nodes and can be filtered by node ID:

* Cluster up-time, number of nodes, number of CPUs, CPU idle gauge
* System load average graph, CPU usage graph by node
* Total memory, available memory gouge, total disk space and available storage gouge
* Memory usage graph by node (used and cached)
* I/O usage graph (read and write Bps)
* IOPS usage (read and write operation per second) and CPU IOWait
* Running containers graph by Swarm service and node
* Network usage graph (inbound Bps, outbound Bps)
* Nodes list (instance, node ID, node name)

***Docker Swarm Services Dashboard***

URL:'https://snapshot.raintank.io/dashboard/snapshot/SyKQ96o2JWfuVyc43hcGgAI9YLcjk3mW?orgId=2'

URL: `http://<swarm-ip>:3000/dashboard/db/docker-swarm-services`

This dashboard shows key metrics for monitoring the resource usage of your Swarm stacks and services, can be filtered by node ID:

* Number of nodes, stacks, services and running container
* Swarm tasks graph by service name
* Health check graph (total health checks and failed checks)
* CPU usage graph by service and by container (top 10)
* Memory usage graph by service and by container (top 10)
* Network usage graph by service (received and transmitted)
* Cluster network traffic and IOPS graphs
* Docker engine container and network actions by node
* Docker engine list (version, node id, OS, kernel, graph driver)

***Prometheus Stats Dashboard***

![Nodes](https://raw.githubusercontent.com/stefanprodan/swarmprom/master/grafana/screens/swarmprom-prometheus-dash-v3.png)

URL: `http://<swarm-ip>:3000/dashboard/db/prometheus`

* Uptime, local storage memory chunks and series
* CPU usage graph
* Memory usage graph
* Chunks to persist and persistence urgency graphs
* Chunks ops and checkpoint duration graphs
* Target scrapes, rule evaluation duration, samples ingested rate and scrape duration graphs
 
 

To use Grafana with Weave Cloud you have to reconfigure the Prometheus data source like this:

* Name: Prometheus
* Type: Prometheus
* Url: https://cloud.weave.works/api/prom
* Access: proxy
* Basic auth: use your service token as password, the user value is ignored

Weave Scope automatically generates a map of your application, enabling you to intuitively understand, 
monitor, and control your microservices based application. 
You can view metrics, tags and metadata of the running processes, containers and hosts. 
Scope offers remote access to the Swarm’s nods and containers, making it easy to diagnose issues in real-time.

![Scope](https://raw.githubusercontent.com/stefanprodan/swarmprom/master/grafana/screens/weave-scope.png)

![Scope Hosts](https://raw.githubusercontent.com/stefanprodan/swarmprom/master/grafana/screens/weave-scope-hosts-v2.png)


Please see the original post and work in this github page 
https://github.com/stefanprodan/swarmprom
This repo is an experiment for research work in Self Adapting µServices Architecture
Thanks to Stefan Prodan for his inspiring work
 
