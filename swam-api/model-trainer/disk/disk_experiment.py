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
import shutil
import os
anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()

DATE_FORMAT = "%m/%d/%y %H:%M"

import disk_generate_data
finalutilityOfdisk = 0.0
# Change this to switch from a matplotlib plot to file output.
PLOT = False
SWARM_CONFIG = {
  "includedFields": [
    {
      "fieldName": "disk",
      "fieldType": "float",
      "maxValue": 100.0,
      "minValue": 0.0
    }
  ],
  "streamDef": {
    "info": "disk",
    "version": 1,
    "streams": [
      {
        "info": "disk.csv",
        "source": "file://disk/disk.csv",
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
    "predictedField": "disk"
  },
  "swarmSize": "medium"
}

def move_model():
  cur_dir = os.getcwd()
  source = os.path.join(cur_dir,'disk/model_0/model_params.py')
  dist = os.path.join(cur_dir,'model_disk.py')
  #print 'dist', dist
  #os.rename(source, dist) 
  print cur_dir, source, dist
  shutil.move(source, dist)

def swarm_over_data():
  cur_dir = os.getcwd()
  dis = distination= os.path.join(cur_dir,'disk')
  outdir = distination= os.path.join(cur_dir,'disk/disk_model_store')
  return permutations_runner.runWithConfig(SWARM_CONFIG,{'overwrite': True }, outDir= outdir, permWorkDir=dis)


def run_disk_experiment():
  input_file = "disk/disk.csv"
  #disk_generate_data.run(input_file)
  disk_params = swarm_over_data()
  model_disk = ModelFactory.create(disk_params)
  model_disk.enableInference({"predictedField": "disk"})
  if PLOT:
    output = NuPICPlotOutput("disk/final_disk_output")
  else:
    output = NuPICFileOutput("disk/final_disk_output")
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
      disk = float(row[1])
      result_disk = model_disk.run({"disk": disk})
      prediction = result_disk.inferences["multiStepBestPredictions"][1]
      anomalyScore = result_disk.inferences['anomalyScore']
      anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(disk, anomalyScore, timestamp)
      sumOfUtilityFitness= sumOfUtilityFitness + (float(disk) * float(anomalyLikelihood))
      sumOfWeaight = sumOfWeaight + float(anomalyLikelihood)
      output.write(timestamp, disk, prediction, anomalyScore)


  output.close()
  print 'sumOfWeaight: ', sumOfWeaight, 'sumOfUtilityFitness: ', sumOfUtilityFitness
  result_output = 'disk/final_disk_output_out.csv'
  utilityOfDisk=0.0
  with open(result_output, "rb") as result_input:
    csv_reader = csv.reader(result_input)

    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    for row in csv_reader:
      anomalyLikelihood = float(row[3])
      utilityOfDisk= utilityOfDisk + (anomalyLikelihood * sumOfUtilityFitness)/sumOfWeaight
    print 'utilityOfDisk: ', utilityOfDisk
  move_model()


 



if __name__ == "__main__":
  run_disk_experiment()
 
