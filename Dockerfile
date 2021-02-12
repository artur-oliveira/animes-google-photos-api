FROM python:3.8.7-slim-buster

RUN mkdir app
WORKDIR /app

RUN pip install --no-cache lxml

COPY requirements.txt requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]