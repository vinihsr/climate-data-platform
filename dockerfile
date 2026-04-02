FROM apache/airflow:2.7.1-python3.9

# Copia o seu requirements para dentro da imagem
COPY requirements.txt /requirements.txt

# Instala tudo de uma vez na build da imagem
RUN pip install --no-cache-dir -r /requirements.txt