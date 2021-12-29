FROM python:3.9-slim-bullseye 

RUN apt-get update && \
    apt-get install -y wget 

RUN /usr/local/bin/python -m pip install --upgrade pip

#RUN apt-get install --no-cache openssl

RUN wget -qO- http://github.com/freeranger/evologger/archive/python3.tar.gz | tar zxf -

WORKDIR /evologger

COPY ./ ./

RUN pip install -r requirements.txt

VOLUME /data

CMD [ "python", "./evologger.py" ]
