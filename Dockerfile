FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lisa_gk_tutor_bot.py .

CMD ["python", "-u", "lisa_gk_tutor_bot.py"]
