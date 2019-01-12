#!/usr/bin/env python
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

"""A simple script to generate a CSV with sine data."""

import csv
import math
import psutil
import datetime
import time
import requests
from nupic.algorithms import anomaly_likelihood

anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()

ROWS = 2500
SECONDS_PER_STEP= 1
DATE_FORMAT = "%m/%d/%y %H:%M"
prometheus='192.168.99.100'
def run(filename="desk.csv"):
  tstart = time.time()
  end = str(tstart+30)
  start = str(tstart)
  print "Generating sine data into %s" % filename
  fileHandle1 = open(filename,"w")
  writer1 = csv.writer(fileHandle1)
  writer1.writerow(["timestamp","disk"])
  writer1.writerow(["datetime","float"])
  writer1.writerow(["",""])
  for i in range(ROWS):
    response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query?query=sum((node_disk_io_time_weighted_seconds_total))%20%2F%20avg(node_disk_io_time_weighted_seconds_total)%20*%20count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~".%2B"%7D)&start='+start+'& end=' + end +'&step=30', timeout=5)
    results = response.json()
    diskData = results['data']['result']
  
    if len(diskData) > 0:
      print 'disk: ', diskData[0]['value']
      diskValue = diskData[0]['value']

      timestamp = datetime.datetime.fromtimestamp(float(diskValue[0])).strftime('%m/%d/%y %H:%M')
      disk = 100 - float(diskValue[0])
      writer1.writerow([timestamp, disk])
    #time.sleep(1)
               
  fileHandle1.close()
  print "Generated %i rows of output data into %s" % (ROWS, filename)


if __name__ == "__main__":
  run()
