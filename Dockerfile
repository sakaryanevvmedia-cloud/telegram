FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .

# Session dosyası için volume mount edilecek
VOLUME /app/session

CMD ["python", "-u", "scraper.py"]
