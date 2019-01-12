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
ROWS = 2500
DATE_FORMAT = "%m/%d/%y %H:%M"
prometheus='192.168.99.100'
def run(filename="cpu.csv"):
  print "Generating sine data into %s" % filename
  fileHandle = open(filename,"w")
  writer = csv.writer(fileHandle)
  writer.writerow(["timestamp","cpu"])
  writer.writerow(["datetime","float"])
  writer.writerow(["",""])
  cpuValue=0
  for i in range(ROWS):
              tstart = time.time()
              end = str(tstart+30)
              start = str(tstart)
              response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query_range?query=sum(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B30s%5D)%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20*%20100%20%2F%20count(node_cpu_seconds_total%7Bmode%3D%22user%22%7D%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~%22.%2B%22%7D)%20&start='+start+'&end='+ end + '&step=30', timeout=5)
              results = response.json()
              cpuData = results['data']['result']
              #cpuData = results['data']['result']
              if len(cpuData) > 0:
                cpuValue = cpuData[0]['values']
                #print (cpuValue[0][0])
                timestamp = datetime.datetime.fromtimestamp(float(cpuValue[0][0])).strftime('%m/%d/%y %H:%M') 
                cpu = 100 - float(cpuValue[0][1])
                writer.writerow([timestamp, cpu])
              ##time.sleep(1)
               
  fileHandle.close()

  print "Generated %i rows of output data into %s" % (ROWS, filename)
 

if __name__ == "__main__":
  run()
