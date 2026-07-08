FROM rasa/rasa:3.6.21-full

WORKDIR /app

USER root

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY actions /app/actions
COPY config /app/config
COPY data /app/data
COPY domain /app/domain
COPY models /app/models

USER 1001

EXPOSE 5005

CMD ["run", "--enable-api", "--cors", "*", "--port", "5005", "--model", "models", "--endpoints", "config/endpoints.yml"]
