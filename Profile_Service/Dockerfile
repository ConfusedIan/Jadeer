FROM python:3.11-slim

WORKDIR /app

# Install shared models package
COPY models/ /models
RUN pip install --no-cache-dir /models

COPY Profile_Service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Profile_Service/ .

EXPOSE 5002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]
