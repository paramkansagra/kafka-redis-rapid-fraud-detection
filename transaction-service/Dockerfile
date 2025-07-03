FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY transaction-service.py .

CMD [ "python3" , "transaction-service.py" ]