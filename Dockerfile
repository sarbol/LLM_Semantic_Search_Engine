FROM python:3.9.12-slim-buster

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . /usr/src/app/

EXPOSE 8000

CMD [ "python", "main.py" ]