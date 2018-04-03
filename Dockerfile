FROM python:3.7

MAINTAINER Andy Challis <andrewchallis@hotmail.co.uk>

ADD requirements.txt

RUN pip install -r requirements.txt