FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 --retries 5 -r /app/requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["python", "src/web.py"]
