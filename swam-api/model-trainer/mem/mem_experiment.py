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
from nupic.algorithms import anomaly_likelihood
import mem_generate_data
import shutil
import os

DATE_FORMAT = "%m/%d/%y %H:%M"
anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()
# Change this to switch from a matplotlib plot to file output.
PLOT = False
finalutilityOfmem=0.0


SWARM_CONFIG = {
  "includedFields": [
    {
      "fieldName": "mem",
      "fieldType": "float",
      "maxValue": 100.0,
      "minValue": 0.0
    }
  ],
  "streamDef": {
    "info": "mem",
    "version": 1,
    "streams": [
      {
        "info": "mem.csv",
        "source": 'file://mem/mem.csv',
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
    "predictedField": "mem"
  },
  "swarmSize": "medium"
}

def move_model():
  cur_dir = os.getcwd()
  source = os.path.join(cur_dir,'mem/model_0/model_params.py')
  dist = os.path.join(cur_dir,'model_mem.py')
  #print 'dist', dist
  #os.rename(source, dist) 
  print cur_dir, source, dist
  shutil.move(source, dist)

def swarm_over_data():
  cur_dir = os.getcwd()
  dist = os.path.join(cur_dir,'mem')
  print 'dist', dist
  outdir = os.path.join(cur_dir,'mem/mem_model_store')
  return permutations_runner.runWithConfig(SWARM_CONFIG,{'maxWorkers': 2, 'overwrite': True }, outDir= outdir, permWorkDir=dist)



def run_mem_experiment():
  cur_dir = os.getcwd()
  input_file = source = os.path.join(cur_dir,'mem/mem.csv')
  print input_file
  #mem_generate_data.run(input_file)
  print 'input_file', input_file
  model_params = swarm_over_data()
  model = ModelFactory.create(model_params)
  model.enableInference({"predictedField": "mem"})
  out_file = 'mem/final_mem.csv'
  if PLOT:
    output = NuPICPlotOutput(out_file)
  else:
    output = NuPICFileOutput(out_file)
  with open(input_file, "rb") as sine_input:
    csv_reader = csv.reader(sine_input)

    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()

    # the real data
    sumOfUtilityFitness=0.0
    sumOfWeaight = 0.0 
    for row in csv_reader:
      timestamp = datetime.datetime.strptime(row[0], DATE_FORMAT)
      mem = float(row[1])
      result = model.run({"mem": mem})
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(mem, anomalyScore, timestamp)
      sumOfUtilityFitness= sumOfUtilityFitness + (float(mem) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      output.write(timestamp, mem, prediction, anomalyScore)

  output.close()
  print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness
  result_output = 'mem/final_mem_out.csv'
  utilityOfmem=0.0
  with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)

    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfmem = utilityOfmem + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
    print 'utilityOfmem: ', utilityOfmem
  move_model()



 



if __name__ == "__main__":
  run_mem_experiment()
