FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py rf_w2v_hoax.pkl /app/

EXPOSE 4998

CMD ["python", "app.py"]