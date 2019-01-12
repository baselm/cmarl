FROM numenta/nupic

MAINTAINER Basel Magableh

RUN apt-get update
RUN apt-get install nano 
RUN apt-get install docker.io -y 


RUN pip install --upgrade pip
RUN pip install --upgrade numpy
RUN pip install --upgrade flask


COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt
 

COPY /model-api /model-api
ENV TERM xterm
 
 
WORKDIR /model-api
CMD python nupic-api.py


