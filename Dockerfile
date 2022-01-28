FROM python:3.9-slim-bullseye

RUN apt-get update && \
    apt-get install -y wget && \
    /usr/local/bin/python -m pip install --upgrade pip

WORKDIR /evologger

COPY ./ ./

RUN pip install -r requirements.txt

CMD [ "python", "./evologger.py" ]
