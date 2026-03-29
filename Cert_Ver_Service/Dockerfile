FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

COPY Cert_Ver_Service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Cert_Ver_Service/ .

EXPOSE 5006

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5006"]
