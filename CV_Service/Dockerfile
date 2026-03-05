FROM python:3.11-slim

WORKDIR /app

COPY CV_Service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CV_Service/ .

EXPOSE 5004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5004"]
