FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir streamlit google-cloud-bigquery pandas db-dtypes requests

EXPOSE 8080
#commande 
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]