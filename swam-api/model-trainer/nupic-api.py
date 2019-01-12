from flask import Flask, request, abort
import csv
from multiprocessing import Pool
from nupic.frameworks.opf.model_factory import ModelFactory
import datetime
import model_cpu
import model_mem
import model_disk
import net_params
from multiprocessing import Process
from nupic.algorithms import anomaly_likelihood
import shutil
import os
import time
import requests
import subprocess
from subprocess import call
import numpy as np
from flask.json import jsonify
import json
from flask import Response
from multiprocessing import Pool
import cpu_adapter
import sys
import json
sys.path.append('mem')
import mem_experiment

sys.path.append('cpu')
import cpu_experiment

sys.path.append('disk')
import disk_experiment
from flask import Flask, request, abort


finalUtilityCpu =0.0
finalutilityDisk =0.0
finalutilityOfmem =0.0
maxU={'metric':'','value':0.0, 'swarmed':False, 'adapted': False, 'msg':''}
result_adapt={}

swarmed=maxU['swarmed']
adapted=maxU['adapted']
def runInParallel(*fns):
  proc = []
  for fn in fns:
    p = Process(target=fn)
    p.start()
    proc.append(p)
  for p in proc:
    p.join()


 


def run_swarm():
    if maxU['swarmed'] == False:
        pool = Pool(processes=3)              # Start a worker processes.
        result = pool.apply_async(disk_experiment.run_disk_experiment)
        result1 = pool.apply_async(cpu_experiment.run_cpu_experiment)
        result2 = pool.apply_async(mem_experiment.run_mem_experiment)
        print result.get(timeout=7600), result1.get(timeout=7600), result2.get(timeout=7600)
     
        #disk_experiment.run_disk_experiment()
        #cpu_experiment.run_cpu_experiment()
        #mem_experiment.run_mem_experiment()
        #runInParallel(disk_experiment.run_disk_experiment(), cpu_experiment.run_cpu_experiment(), mem_experiment.run_mem_experiment())
        print "swarm finished "
        maxU['swarmed'] =True
        maxU['msg'] ='swarm finished'
    else:
        print "No need to swarm  already done"
        maxU['msg'] ='No need to swarm  already done'

    return True

def callback():
    return "swarm finished in subprocess "

anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()
DATE_FORMAT = "%m/%d/%y %H:%M"
finalUtilityCpu=0.0 
SECONDS_PER_STEP= 15
adaptresult = {'metric': ' ', 'value':0, 'cost':0}
adaptoutcome = {'metric': ' ', 'value':0, 'cost':0, 'msg':''}
results=0
resultsA= []
prometheus='192.168.99.100'
app = Flask(__name__)
aresult = {'metric': ' ', 'value':0, 'prediction':0, 'anomalyScore':0,'anomalyLikelihood':0}
 
@app.route('/start')
def startSwarm():
    swarmed=maxU['swarmed']
    print 'swarmed', swarmed
    if swarmed==False:

        print "no swarm found !"
        
        swarmed= run_swarm()
        maxU['swarmed'] = swarmed
    elif swarmed==True: 
         maxU['swarmed'] = True
         maxU['msg'] ="No need to swarm"

    

    return json.dumps(maxU)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        swarmed=maxU['swarmed']
        pool = Pool(processes=1)
        result = pool.apply_async(cpu_adapter.run, () , callback)
        print 'result_adapt: ', result
        print(request.json)
        return '', 200
    else:
        abort(400)

@app.route('/mem')
def get_mem_observation():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    model_mem_model = ModelFactory.create(model_mem.MODEL_PARAMS)
    model_mem_model.enableInference({"predictedField": "mem"})
    response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query_range?query=sum((node_memory_MemAvailable_bytes%20%2F%20node_memory_MemTotal_bytes)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D%20*%20100)%20%2F%20count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)&start='+start+'&end='+ end +'&step=30', timeout=5)
    results = response.json()
    memData = results['data']['result']
    result = 0
    prediction = 0
    anomalyScore = 0
    anomalyLikelihood = 0 
    utility_mem = 0 
    mem  = 0
    js = None 
    if len(memData) > 0:
        #print(memData)
        memValue = memData[0]['values']
        #print(memValue)
        timestamp = datetime.datetime.fromtimestamp(float(memValue[0][0])).strftime('%m/%d/%y %H:%M')
        mem = 100 - float(memValue[0][1])
        #print 'time: ', timestamp, ' mem Usage: ',mem 
        result = model_mem_model.run({"mem": mem})
        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences['anomalyScore']
        anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(mem, anomalyScore, timestamp)
         
        utility_mem =  anomalyLikelihood * mem 
        data = {
        'mem'  : float(mem),
        'prediction' : float(prediction), 
        'anomalyScore': float(anomalyScore), 
        'anomalyLikelihood':float(anomalyLikelihood), 
        'utility_mem':float(utility_mem)
            }
        js = json.dumps(data)
    else: 
        data = {
        'mem'  : float(0.0),
        'prediction' : float(0), 
        'anomalyScore': float(0), 
        'anomalyLikelihood':float(0), 
        'utility_mem':float(0)
            }
        js = json.dumps(data)

       
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Link'] = 'http://nupicapi.8888'
    return resp
    
    return np.array(mem_axis) 
@app.route('/disk')
def get_disk_observation():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    model_disk_model = ModelFactory.create(model_disk.MODEL_PARAMS)
    model_disk_model.enableInference({"predictedField": "disk"})
    response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query?query=sum((node_disk_io_time_weighted_seconds_total))%20%2F%20avg(node_disk_io_time_weighted_seconds_total)%20*%20count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~".%2B"%7D)&start='+start+'& end=' + end +'&step=30', timeout=5)
    results = response.json()
    diskData = results['data']['result']
    result = 0
    prediction = 0
    anomalyScore = 0
    anomalyLikelihood = 0 
    utility_disk = 0 
    disk  = 0
    js= None
    if len(diskData) > 0:
        diskValue = diskData[0]['value']
        timestamp = datetime.datetime.fromtimestamp(float(diskValue[0])).strftime('%m/%d/%y %H:%M')
        disk = 100 - float(diskValue[1])
        #print 'time: ', timestamp,' disk Usage: ',disk 
        result = model_disk_model.run({"disk": disk})
        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences['anomalyScore']
        anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(disk, anomalyScore, timestamp)

        utility_disk = anomalyLikelihood * disk  
        data = {
        'disk'  : float(disk),
        'prediction' : float(prediction), 
        'anomalyScore': float(anomalyScore), 
        'anomalyLikelihood':float(anomalyLikelihood), 
        'utility_disk':float(utility_disk)
            }
        js = json.dumps(data)
    else: 
        data = {
        'disk'  : float(0.0),
        'prediction' : float(0), 
        'anomalyScore': float(0), 
        'anomalyLikelihood':float(0), 
        'utility_disk':float(0)
            }
        js = json.dumps(data)

       
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Link'] = 'http://nupicapi.8888'

    return resp
@app.route('/net')
def get_net_observation():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    model_net = ModelFactory.create(net_params.MODEL_PARAMS)
    model_net.enableInference({"predictedField": "bytes_sent"})
    response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query?query=sum(rate(container_network_receive_bytes_total%7Bcontainer_label_com_docker_swarm_node_id%3D~".%2B"%7D%5B30s%5D))%20by%20(container_label_com_docker_swarm_service_name)&start='+start+'& end='+ end + '&step=30', timeout=5)
    results = response.json()
    diskData = results['data']['result']
    result = 0
    prediction = 0
    anomalyScore = 0
    anomalyLikelihood = 0 
    utility_net = 0 
    net  = 0
    js = None 
    if len(diskData) > 0:
        diskValue = diskData[0]['value']
        timestamp = datetime.datetime.fromtimestamp(float(diskValue[0])).strftime('%m/%d/%y %H:%M')
        net = float(diskValue[1])
        #print 'time: ', timestamp,' net bytes_sent: ',net 
        result = model_net.run({"bytes_sent": net})
        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences['anomalyScore']
        anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(net, anomalyScore, timestamp)
        utility_net = anomalyLikelihood * net   
        data = {
        'net'  : float(net),
        'prediction' : float(prediction), 
        'anomalyScore': float(anomalyScore), 
        'anomalyLikelihood':float(anomalyLikelihood), 
        'utility_net':float(utility_net)
            }
        js = json.dumps(data)
    else: 
        data = {
        'net'  : float(0),
        'prediction' : float(0), 
        'anomalyScore': float(0), 
        'anomalyLikelihood':float(0), 
        'utility_net':float(0)
            }
        js = json.dumps(data)

       
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Link'] = 'http://nupicapi.8888/net'
    return resp

@app.route('/')
def hi():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    msg= "<h1> Hi Welcome to Adaptation Manager IP: " + prometheus  +  " start time: " + str(start)  +  " end time: " + str(end) 
    return msg 
@app.route('/cpu')
def get_cpu_observation():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    model_cpu_model = ModelFactory.create(model_cpu.MODEL_PARAMS)
    model_cpu_model.enableInference({"predictedField": "cpu"})
    #response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query?query=sum(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B30s%5D)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20*%20100%20%2F%20count(node_cpu%7Bmode%3D%22user%22%7D%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20&start=1544788200&end=1544788260&step=30', timeout=5)
    response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query_range?query=sum(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B30s%5D)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20*%20100%20%2F%20count(node_cpu_seconds_total%7Bmode%3D%22user%22%7D%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20&start='+start+'&end='+ end + '&step=30', timeout=5)

    results = response.json()
    cpuData = results['data']['result']
    result = 0
    prediction = 0
    anomalyScore = 0
    anomalyLikelihood = 0 
    utility_cpu = 0 
    cpu  = 0    
    js = None 
    if len(cpuData) > 0:
        
        cpuValue = cpuData[0]['values']
        #print (cpuValue[0][0])
        timestamp = datetime.datetime.fromtimestamp(float(cpuValue[0][0])).strftime('%m/%d/%y %H:%M') 
        cpu = 100 - float(cpuValue[0][1])
       
        result = model_cpu_model.run({"cpu": cpu})
        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences['anomalyScore']
        anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(cpu, anomalyScore, timestamp)
        utility_cpu = anomalyLikelihood * cpu 
        #print 'time: ', timestamp, ' cpu Usage: ',cpu , 'utility_cpu: ', utility_cpu
        #cpu_axis=[cpu, prediction, anomalyScore, anomalyLikelihood, utility_cpu]
        data = {
        'cpu'  : float(cpu),
        'prediction' : float(prediction), 
        'anomalyScore': float(anomalyScore), 
        'anomalyLikelihood':float(anomalyLikelihood), 
        'utility_cpu':float(utility_cpu)
            }
        js = json.dumps(data)
    else: 
        data = {
        'cpu'  : float(0),
        'prediction' : float(0), 
        'anomalyScore': float(0), 
        'anomalyLikelihood':float(0), 
        'utility_cpu':float(0)
            }
        js = json.dumps(data)
    
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Link'] = 'http://nupicapi.8888'
    return resp

@app.route('/data')
def get_observation():
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    obs = None 
    disk_axis = get_disk_observation()
    mem_axis  = get_mem_observation()
    cpu_axis  = get_cpu_observation()
    net_axis  = get_net_observation()
    data = {
        'cpu'  : disk_axis,
        'mem' : mem_axis, 
        'net': net_axis 
         }
    print (data)
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Link'] = 'http://nupicapi.8888'
    return data
      
     
    
    return str(response)

if __name__ == '__main__':
    tstart = time.time()
    end = str(tstart+30)
    start = str(tstart)
    app.run(host='0.0.0.0', port='8888', debug=True)
