#!/usr/bin/python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import csv
from multiprocessing import Pool
from nupic.frameworks.opf.model_factory import ModelFactory
import datetime
import model_cpu
import model_mem
import model_disk
from multiprocessing import Process
from nupic.algorithms import anomaly_likelihood
import shutil
import os
import time
import requests
anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()

# Change this to switch from a matplotlib plot to file output.
DATE_FORMAT = "%m/%d/%y %H:%M"
finalUtilityCpu=0.0 
SECONDS_PER_STEP= 15
adaptresult = {'metric': ' ', 'value':0, 'cost':0}
adaptoutcome = {'metric': ' ', 'value':0, 'cost':0, 'msg':''}

resultsA= []

def run_disk_adapter():
   model_disk_model = ModelFactory.create(model_disk.MODEL_PARAMS)
   model_disk_model.enableInference({"predictedField": "disk"})
   uc =0.0
   filename = 'disk_adapt.csv'
   fileHandle1 = open(filename,"w")
   writer1 = csv.writer(fileHandle1)
   writer1.writerow(['timestamp', 'disk', 'prediction', 'anomalyScore', 'anomalyLikelihood', 'sumOfUtilityFitness', 'sumOfUtilityFitnessPredicted', 'sumOfscore', 'sumOfWeaight', 'Uprev' , 'diffChange'] )

   sumOfUtilityFitness=0.0
   sumOfWeaight = 0.0 
   Uprev = 0
   Wprev = 0 
   diffChange=0 
   Udisk=0
   Upredicted=0 
   sumOfscore=0
   sumOfUtilityFitnessPredicted=0
   utilityOfDiskPredicted=0
   for x in range(1,300):
      response = requests.get('http://admin:admin@prometheus:9090/api/v1/query?query=sum((node_filesystem_free%7Bmountpoint%3D%22%2F%22%7D%20%2F%20node_filesystem_size%7Bmountpoint%3D%22%2F%22%7D)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D%20*%20100)%20%2F%20count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)&start=1538181830&end=1538182730&step=30', timeout=5)
      results = response.json()
      cpuData = results['data']['result'] 
      if len(cpuData) > 0:
        cpuValue = cpuData[0]['value']
        timestamp = datetime.datetime.fromtimestamp(float(cpuValue[0])).strftime('%m/%d/%y %H:%M')
         
      disk = 100 - float(cpuValue[1])
      print 'time: ', timestamp,'irate: ', x, ' disk Usage: ',disk 
      result = model_disk_model.run({"disk": disk})
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(disk, anomalyScore, timestamp)

      #uc= (anomalyLikelihood * cpu + prediction * anomalyLikelihood )/(anomalyLikelihood + anomalyLikelihood) 
      #calculate equ 1 in paper 
      sumOfUtilityFitness= sumOfUtilityFitness + (float(disk) * float(anomalyLikelihood))
      sumOfUtilityFitnessPredicted= sumOfUtilityFitnessPredicted + (float(prediction) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      sumOfscore = sumOfscore + float(anomalyScore)

      #calculate equ 3 in paper 
  

      #calculate equ 4 in paper 
      Ucurr = (float(disk) * float(anomalyLikelihood))  
      diffChange = diffChange  + (Ucurr - Uprev)
      Uprev = Ucurr
      writer1.writerow([timestamp, disk, prediction, anomalyScore, anomalyLikelihood, sumOfUtilityFitness, sumOfUtilityFitnessPredicted, sumOfscore, sumOfWeaight, Uprev , diffChange] )
      
      try:
        time.sleep(2)
      except:
        pass
   fileHandle1.close()
   print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness, 'sumOfUtilityFitnessPredicted: ', sumOfUtilityFitnessPredicted, 'diffChange: ', diffChange 
   result_output = 'disk_adapt.csv'
   utilityOfdisk=0.0
   utilityOfdiskPredicted=0.0
   with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfdisk= utilityOfdisk + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
      utilityOfdiskPredicted= utilityOfdiskPredicted + (anomalyLikelihood * sumOfUtilityFitnessPredicted)/sumOfWeaight

    cost = round((utilityOfdisk - utilityOfdiskPredicted) * (sumOfWeaight * sumOfscore)/(diffChange * 5.34),0)
    print 'utilityOfdisk: ', utilityOfdisk, 'cost: ', cost
    adaptresult['metric'] = 'utilityOfdisk'
    adaptresult['value'] = utilityOfdisk
    adaptresult['cost'] = cost
    resultsA.append(adaptresult.copy())


def run_mem_adapter():
   model_mem_model = ModelFactory.create(model_mem.MODEL_PARAMS)
   model_mem_model.enableInference({"predictedField": "mem"})
   uc =0.0
   filename = 'mem_adapt.csv'
   fileHandle1 = open(filename,"w")
   writer1 = csv.writer(fileHandle1)
   writer1.writerow(['timestamp', 'mem', 'prediction', 'anomalyScore', 'anomalyLikelihood', 'sumOfUtilityFitness', 'sumOfUtilityFitnessPredicted', 'sumOfscore', 'sumOfWeaight', 'Uprev' , 'diffChange'] )

   sumOfUtilityFitness=0.0
   sumOfWeaight = 0.0 
   Uprev = 0
   Wprev = 0 
   diffChange=0 
   utilityOfmem=0
   Upredicted=0 
   sumOfscore=0
   sumOfUtilityFitnessPredicted=0
   utilityOfmemPredicted=0
   for x in range(1,300):
      response = requests.get('http://admin:admin@prometheus:9090/api/v1/query?query=sum((node_memory_MemAvailable%20%2F%20node_memory_MemTotal)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D%20*%20100)%20%2F%20count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)&start=1538181656&end=1538182556&step=30', timeout=5)
      results = response.json()
      memData = results['data']['result'] 
      if len(memData) > 0:
        memValue = memData[0]['value']
        timestamp = datetime.datetime.fromtimestamp(float(memValue[0])).strftime('%m/%d/%y %H:%M')
        
      mem = 100 - float(memValue[1])
      print 'time: ', timestamp,'irate: ', x, ' mem Usage: ',mem 
      result = model_mem_model.run({"mem": mem})
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(mem, anomalyScore, timestamp)

      #uc= (anomalyLikelihood * cpu + prediction * anomalyLikelihood )/(anomalyLikelihood + anomalyLikelihood) 
      #calculate equ 1 in paper 
      sumOfUtilityFitness= sumOfUtilityFitness + (float(mem) * float(anomalyLikelihood))
      sumOfUtilityFitnessPredicted= sumOfUtilityFitnessPredicted + (float(prediction) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      sumOfscore = sumOfscore + float(anomalyScore)

      #calculate equ 3 in paper 
  

      #calculate equ 4 in paper 
      Ucurr = (float(mem) * float(anomalyLikelihood))  
      diffChange = diffChange  + (Ucurr - Uprev)
      Uprev = Ucurr
      writer1.writerow([timestamp, mem, prediction, anomalyScore, anomalyLikelihood, sumOfUtilityFitness, sumOfUtilityFitnessPredicted, sumOfscore, sumOfWeaight, Uprev , diffChange] )
      
      try:
        time.sleep(2)
      except:
        pass
   fileHandle1.close()
   print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness, 'sumOfUtilityFitnessPredicted: ', sumOfUtilityFitnessPredicted, 'diffChange: ', diffChange 
   result_output = 'mem_adapt.csv'
   utilityOfCpu=0.0
   with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfmem= utilityOfmem + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
      utilityOfmemPredicted= utilityOfmemPredicted + (anomalyLikelihood * sumOfUtilityFitnessPredicted)/sumOfWeaight

    cost = round((utilityOfmem - utilityOfmemPredicted) * (sumOfWeaight * sumOfscore)/(diffChange * 5.34),0)
    print 'utilityOfMem: ', utilityOfmem, 'cost: ', cost
    adaptresult['metric'] = 'utilityOfMem'
    adaptresult['value'] = utilityOfmem
    adaptresult['cost'] = cost
    resultsA.append(adaptresult.copy())




def run_cpu_adapter():
   model_cpu_model = ModelFactory.create(model_cpu.MODEL_PARAMS)
   model_cpu_model.enableInference({"predictedField": "cpu"})
   uc =0.0
   filename = 'cpu_adapt.csv'
   fileHandle1 = open(filename,"w")
   writer1 = csv.writer(fileHandle1)
   writer1.writerow(['timestamp', 'cpu', 'prediction', 'anomalyScore', 'anomalyLikelihood', 'sumOfUtilityFitness', 'sumOfUtilityFitnessPredicted', 'sumOfscore', 'sumOfWeaight', 'Uprev' , 'diffChange'] )

   sumOfUtilityFitness=0.0
   sumOfWeaight = 0.0 
   Uprev = 0
   Wprev = 0 
   diffChange=0 
   Ucpu=0
   Upredicted=0 
   sumOfscore=0
   sumOfUtilityFitnessPredicted=0
   utilityOfCpuPredicted=0
   for x in range(1,300):
      response = requests.get('http://admin:admin@prometheus:9090/api/v1/query?query=sum(irate(node_cpu%7Bmode%3D%22idle%22%7D%5B30s%5D)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20*%20100%20%2F%20count(node_cpu%7Bmode%3D%22user%22%7D%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20&start=1538182792&end=1538182852&step=30', timeout=5)
      results = response.json()
      cpuData = results['data']['result'] 
      if len(cpuData) > 0:
        cpuValue = cpuData[0]['value']
        timestamp = datetime.datetime.fromtimestamp(float(cpuValue[0])).strftime('%m/%d/%y %H:%M')
         
      cpu = 100 - float(cpuValue[1])
      print 'time: ', timestamp,  'irate: ', x, ' cpu Usage: ',cpu 
      result = model_cpu_model.run({"cpu": cpu})
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(cpu, anomalyScore, timestamp)

      #uc= (anomalyLikelihood * cpu + prediction * anomalyLikelihood )/(anomalyLikelihood + anomalyLikelihood) 
      #calculate equ 1 in paper 
      sumOfUtilityFitness= sumOfUtilityFitness + (float(cpu) * float(anomalyLikelihood))
      sumOfUtilityFitnessPredicted= sumOfUtilityFitnessPredicted + (float(prediction) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      sumOfscore = sumOfscore + float(anomalyScore)

      #calculate equ 3 in paper 
  

      #calculate equ 4 in paper 
      Ucurr = (float(cpu) * float(anomalyLikelihood))  
      diffChange = diffChange  + (Ucurr - Uprev)
      Uprev = Ucurr
      writer1.writerow([timestamp, cpu, prediction, anomalyScore, anomalyLikelihood, sumOfUtilityFitness, sumOfUtilityFitnessPredicted, sumOfscore, sumOfWeaight, Uprev , diffChange] )
      
      try:
        time.sleep(2)
      except:
        pass
   fileHandle1.close()
   print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness, 'sumOfUtilityFitnessPredicted: ', sumOfUtilityFitnessPredicted, 'diffChange: ', diffChange 
   result_output = 'cpu_adapt.csv'
   utilityOfCpu=0.0
   with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfCpu= utilityOfCpu + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
      utilityOfCpuPredicted= utilityOfCpuPredicted + (anomalyLikelihood * sumOfUtilityFitnessPredicted)/sumOfWeaight

    cost = round((utilityOfCpu - utilityOfCpuPredicted) * (sumOfWeaight * sumOfscore)/(diffChange * 5.34),0)
    print 'utilityOfCpu: ', utilityOfCpu, 'cost: ', cost
    adaptresult['metric'] = 'utilityOfCpu'
    adaptresult['value'] = utilityOfCpu
    adaptresult['cost'] = cost
    resultsA.append(adaptresult.copy())

def runInParallel(*fns):
  proc = []
  for fn in fns:
    p = Process(target=fn)
    p.start()
    proc.append(p)
  for p in proc:
    p.join()
  return resultsA
def scaleMemeory():
  print 'Scaling memory'
  pass
def scaleCPU():
  print 'Scaling scaleCPU'
  pass
def scaledisk():
  print 'Scaling scaledisk'
  pass
def callback():
  return "Process finished"
def run():
  pool = Pool(processes=3)
  result = pool.apply_async(run_cpu_adapter)
  result1 = pool.apply_async(run_mem_adapter)
  result2 = pool.apply_async(run_disk_adapter)
  print result.get(timeout=800), result1.get(timeout=800), result2.get(timeout=800)
  maxU = 0
  metric = ''
  cost = ''

  for i in resultsA:
    print "*** ", i 
    if float(i['value']) > maxU:
      adaptoutcome['value'] = float(i['value'])
      adaptoutcome['metric'] = i['metric']
      adaptoutcome['cost'] = i['cost']

  
  print "==> ", maxU, metric, cost
  if metric == 'utilityOfMem':

    scaleMemeory()
    adaptoutcome['msg'] = 'scaleMemeory'
  elif metric == 'utilityOfCpu':
    scaleCPU()
    adaptoutcome['msg'] = 'scaleCPU'
  elif metric == 'utilityOfdisk':
    scaledisk()
    adaptoutcome['msg'] = 'scaledisk'
  return adaptoutcome

if __name__ == "__main__":
  theResult = run()
  print theResult

