FROM python:3.11-slim

WORKDIR /app

# Install shared models package
COPY models/ /models
RUN pip install --no-cache-dir /models

COPY SkillsAssement/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY SkillsAssement/ .

EXPOSE 5003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5003"]
