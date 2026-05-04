FROM python:3.11-slim

LABEL authors="henryzord"
LABEL name="ngo-ccsh-backend"
LABEL description="Dockerfile para instalar dependências e fazer configuração inicial do backend do NGO do CCSH"
LABEL version="0.1"

# A pasta raiz é a pasta de trabalho do projeto
WORKDIR /home

# cria diretório não-versionado instance
RUN mkdir instance

# Copia diretórios locais para o diretório da imagem do docker
COPY . .

# necessário para instalar o ibm_db no Linux
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2 \
    locales

RUN rm -rf /var/lib/apt/lists/* && \
    sed -i '/^#.* pt_BR.UTF-8 /s/^#//' /etc/locale.gen && \
    locale-gen

# Instala os pacotes do arquivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /home/backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]