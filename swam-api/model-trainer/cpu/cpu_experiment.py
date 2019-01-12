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
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic_output import NuPICFileOutput, NuPICPlotOutput
from nupic.swarming import permutations_runner
import datetime
import cpu_generate_data
from multiprocessing import Process
from nupic.algorithms import anomaly_likelihood
import shutil
import os
anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()

# Change this to switch from a matplotlib plot to file output.
DATE_FORMAT = "%m/%d/%y %H:%M"
PLOT = False
finalUtilityCpu=0.0 
SWARM_CONFIG = {
  "includedFields": [
    {
      "fieldName": "cpu",
      "fieldType": "float",
      "maxValue": 100.0,
      "minValue": 0.0
    }
  ],
  "streamDef": {
    "info": "cpu",
    "version": 1,
    "streams": [
      {
        "info": "cpu.csv",
        "source": "file://cpu/cpu.csv",
        "columns": [
          "*"
        ]
      }
    ]
  },
  "inferenceType": "TemporalAnomaly",
  "inferenceArgs": {
    "predictionSteps": [
      1
    ],
    "predictedField": "cpu"
  },
  "swarmSize": "medium"
}


#medium

def move_model():
  cur_dir = os.getcwd()
  source = os.path.join(cur_dir,'cpu/model_0/model_params.py')
  dist = os.path.join(cur_dir,'model_cpu.py')
  #print 'dist', dist
  #os.rename(source, dist) 
  print cur_dir, source, dist
  shutil.move(source, dist)

def swarm_over_data(SWARM_CONFIG):
  cur_dir = os.getcwd()
  dis = os.path.join(cur_dir,'cpu')
  outdir =  os.path.join(cur_dir,'cpu/cpu_model_store')
  return permutations_runner.runWithConfig(SWARM_CONFIG,{'maxWorkers': 8, 'overwrite': True }, outDir= outdir, permWorkDir=dis)
  


def run_cpu_experiment():
  input_file = "cpu.csv"
  cur_dir = os.getcwd()
  input_file = os.path.join(cur_dir,'cpu/cpu.csv')
  #cpu_generate_data.run(input_file)
  model_params = swarm_over_data(SWARM_CONFIG)
  model = ModelFactory.create(model_params)
  model.enableInference({"predictedField": "cpu"})
  if PLOT:
    output = NuPICPlotOutput("cpu/final_cpu_output")
  else:
    output = NuPICFileOutput("cpu/final_cpu_output")

  with open(input_file, "rb") as cpu_input:
    csv_reader = csv.reader(cpu_input)
    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    # the real data
    sumOfUtilityFitness=0.0
    sumOfWeaight = 0.0 
    for row in csv_reader:
      timestamp = datetime.datetime.strptime(row[0], DATE_FORMAT)
      cpu = float(row[1])
      result = model.run({"cpu": cpu})
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(cpu, anomalyScore, timestamp)
      uc= (anomalyLikelihood * cpu + prediction * anomalyLikelihood )/(anomalyScore + anomalyLikelihood) 
      sumOfUtilityFitness= sumOfUtilityFitness + (float(cpu) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      output.write(timestamp, cpu, prediction, anomalyScore)

  output.close()

  print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness
  result_output = 'cpu/final_cpu_output_out.csv'
  utilityOfCpu=0.0
  with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)

    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfCpu= utilityOfCpu + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
    print 'utilityOfCpu: ', utilityOfCpu

  move_model()
if __name__ == "__main__":
  run_cpu_experiment()
