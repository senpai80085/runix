FROM python:3.11-slim
WORKDIR /app
RUN pip install flask gunicorn
COPY app.py .
ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 app:app
