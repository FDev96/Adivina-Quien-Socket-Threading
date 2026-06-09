FROM python:3.11-slim

WORKDIR /app

COPY . .

EXPOSE 8080 8765

CMD ["python", "server.py"]
