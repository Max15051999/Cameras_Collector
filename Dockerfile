FROM python:3.9

RUN mkdir -p /usr/src/app/

WORKDIR /usr/src/app/

COPY . /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt-get install wget -y \
    && apt-get install postgis -y

EXPOSE 5432

CMD ["python", "parser.py"]