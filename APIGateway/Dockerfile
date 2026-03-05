FROM python:3.11-slim

WORKDIR /app

COPY models/ /models
RUN pip install --no-cache-dir /models

COPY APIGateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY APIGateway/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
