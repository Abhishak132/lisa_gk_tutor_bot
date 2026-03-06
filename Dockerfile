WORKDIR /app

# Dependencies pehle copy karo (cache ke liye)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot file copy karo
COPY lisa_gk_tutor_bot.py .

# Run karo
CMD ["python", "-u", "lisa_gk_tutor_bot.py"]
