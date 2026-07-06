FROM virpanuatacr.azurecr.io/app/python:3.12.5-slim
COPY . /app
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5500

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5500"]