FROM python:3.11-slim

ENV PYTHONFAULTHANDLER=1 \
     PYTHONUNBUFFERED=1 \
     PYTHONDONTWRITEBYTECODE=1 \
     PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir

CMD ["python", "bot.py"]
