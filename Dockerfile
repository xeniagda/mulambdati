FROM python:3.8
WORKDIR /usr/src/app/server/
COPY requirements.txt /usr/src/
RUN apt-get update
RUN apt-get install -y wamerican
RUN pip install -r /usr/src/requirements.txt
COPY . .
CMD [ "python", "web_api.py", "4080" ]
